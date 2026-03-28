from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.chunking.semantic_chunker import SemanticChunker
from app.core.cache import InMemoryCache
from app.core.config import RetrievalSettings
from app.core.telemetry import TelemetryCollector
from app.ingestion.ingestor import DocumentIngestor
from app.parsing.pdf_parser import PdfParser, PdfParserConfig
from app.qa.citation import CitationAssembler
from app.qa.llm import LLMClient
from app.qa.question_router import QuestionRouter
from app.qa.service import QAService
from app.retrieval.bm25_store import BM25Store
from app.retrieval.faiss_store import FaissStore
from app.retrieval.hybrid import HybridRetriever
from app.tables.table_qa import TableQAEngine

try:
    import fitz  # type: ignore
except Exception:
    fitz = None


class DummyEmbedder:
    def encode(self, texts: Iterable[str]) -> np.ndarray:
        vectors: list[list[float]] = []
        for text in texts:
            vectors.append([float(len(text)), float(sum(char.isdigit() for char in text) + 1)])
        return np.array(vectors, dtype="float32")


def test_pipeline_end_to_end_with_generated_documents(tmp_path: Path) -> None:
    """Full ingest + retrieval + QA flow works on generated real files."""

    if fitz is None:
        return
    dataset_root = tmp_path / "dataset"
    company_dir = dataset_root / "Acme"
    company_dir.mkdir(parents=True)

    pdf_path = company_dir / "report.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Acme management commentary for 2023. Revenue expanded.")
    document.save(str(pdf_path))
    document.close()

    xlsx_path = company_dir / "financials.xlsx"
    pd.DataFrame({"Metric": ["Revenue"], "2023": ["1000"]}).to_excel(xlsx_path, index=False)

    json_path = company_dir / "company.json"
    json_path.write_text(json.dumps({"company": "Acme", "country": "UZ"}), encoding="utf-8")

    embedder = DummyEmbedder()
    retriever = HybridRetriever(
        text_store=FaissStore(embedder),
        table_store=FaissStore(embedder),
        bm25_store=BM25Store(),
        settings=RetrievalSettings(text_top_k=5, table_top_k=5),
    )
    ingestor = DocumentIngestor(
        chunker=SemanticChunker(),
        retriever=retriever,
        pdf_parser=PdfParser(PdfParserConfig(enable_ocr=False)),
        incremental=False,
    )
    ingestion_result = ingestor.ingest(dataset_root)
    assert ingestion_result.processed_files == 3
    assert not ingestion_result.failed_files
    assert ingestion_result.text_chunks
    assert ingestion_result.table_chunks

    qa_service = QAService(
        retriever=retriever,
        table_qa=TableQAEngine(),
        llm_client=LLMClient(endpoint=None, api_key=None),
        cache=InMemoryCache(ttl_seconds=60),
        question_router=QuestionRouter(),
        citation_assembler=CitationAssembler(),
        telemetry=TelemetryCollector(window_size=100),
    )

    numeric_response = qa_service.answer("What is revenue in 2023?", company="Acme")
    assert "Revenue" in numeric_response.answer
    assert numeric_response.relevant_chunks

    narrative_response = qa_service.answer("What does management commentary mention?", company="Acme")
    assert narrative_response.answer
