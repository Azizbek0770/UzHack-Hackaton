from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

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


def run() -> None:
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is required for smoke test.")
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_root = Path(temp_dir) / "dataset"
        company_dir = dataset_root / "Acme"
        company_dir.mkdir(parents=True)

        pdf_path = company_dir / "report.pdf"
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), "Acme management commentary for 2023. Revenue expanded strongly.")
        document.save(str(pdf_path))
        document.close()

        xlsx_path = company_dir / "financials.xlsx"
        pd.DataFrame({"Metric": ["Revenue", "Profit"], "2023": ["1000", "230"]}).to_excel(
            xlsx_path,
            index=False,
        )

        json_path = company_dir / "company.json"
        json_path.write_text(
            json.dumps({"company": "Acme", "country": "Uzbekistan"}, ensure_ascii=False),
            encoding="utf-8",
        )

        retriever = HybridRetriever(
            text_store=FaissStore(DummyEmbedder()),
            table_store=FaissStore(DummyEmbedder()),
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
        qa_service = QAService(
            retriever=retriever,
            table_qa=TableQAEngine(),
            llm_client=LLMClient(endpoint=None, api_key=None),
            cache=InMemoryCache(ttl_seconds=60),
            question_router=QuestionRouter(),
            citation_assembler=CitationAssembler(),
            telemetry=TelemetryCollector(window_size=100),
        )

        response = qa_service.answer("What is revenue in 2023?", company="Acme")
        print(
            json.dumps(
                {
                    "processed_files": ingestion_result.processed_files,
                    "failed_files": len(ingestion_result.failed_files),
                    "text_chunks": len(ingestion_result.text_chunks),
                    "table_chunks": len(ingestion_result.table_chunks),
                    "answer": response.answer,
                    "sources": [source.model_dump() for source in response.relevant_chunks],
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    run()
