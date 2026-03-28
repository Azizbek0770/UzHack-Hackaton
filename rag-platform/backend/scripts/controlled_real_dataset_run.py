from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.chunking.semantic_chunker import SemanticChunker
from app.core.audit_db import AuditStore
from app.core.cache import InMemoryCache
from app.core.config import RetrievalSettings, get_settings
from app.core.telemetry import TelemetryCollector
from app.ingestion.ingestor import DocumentIngestor
from app.ingestion.manifest import IngestionManifest
from app.ingestion.reporting import IngestionReportStore
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


def _write_company_documents(root: Path, company: str, year: int, revenue: int, profit: int) -> None:
    company_dir = root / company
    company_dir.mkdir(parents=True, exist_ok=True)

    if fitz is not None:
        pdf_path = company_dir / "management_report.pdf"
        document = fitz.open()
        page = document.new_page()
        page.insert_text(
            (72, 72),
            f"{company} management commentary for {year}. Strategy focuses on exports and risk control.",
        )
        page2 = document.new_page()
        page2.insert_text((72, 72), f"Выручка компании за {year} укрепилась благодаря операционной эффективности.")
        document.save(str(pdf_path))
        document.close()

    xlsx_path = company_dir / "financials.xlsx"
    pd.DataFrame(
        {
            "Metric": ["Revenue", "Profit"],
            str(year): [str(revenue), str(profit)],
        }
    ).to_excel(xlsx_path, index=False)

    metadata_path = company_dir / "company.json"
    metadata_path.write_text(
        json.dumps(
            {
                "company": company,
                "country": "Uzbekistan",
                "currency": "UZS",
                "report_year": year,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def run() -> None:
    settings = get_settings()
    dataset_path = Path(settings.controlled_dataset_path)
    dataset_path.mkdir(parents=True, exist_ok=True)
    _write_company_documents(dataset_path, "Acme", 2024, 1500, 320)
    _write_company_documents(dataset_path, "Beta", 2024, 980, 210)

    retriever = HybridRetriever(
        text_store=FaissStore(DummyEmbedder()),
        table_store=FaissStore(DummyEmbedder()),
        bm25_store=BM25Store(),
        settings=RetrievalSettings(text_top_k=6, table_top_k=6),
    )
    report_store = IngestionReportStore(Path(settings.ingestion_report_file))
    manifest = IngestionManifest(Path(settings.ingestion_manifest_file))
    ingestor = DocumentIngestor(
        chunker=SemanticChunker(),
        retriever=retriever,
        pdf_parser=PdfParser(
            PdfParserConfig(
                enable_ocr=settings.ocr_enabled,
                ocr_language_mode=settings.ocr_language_mode,
                ocr_min_confidence=settings.ocr_min_confidence,
            )
        ),
        manifest=manifest,
        incremental=False,
        report_store=report_store,
    )
    ingestion_result = ingestor.ingest(dataset_path)
    index_directory = Path(settings.index_directory)
    retriever.save(index_directory)

    qa_service = QAService(
        retriever=retriever,
        table_qa=TableQAEngine(),
        llm_client=LLMClient(endpoint=None, api_key=None),
        cache=InMemoryCache(ttl_seconds=300),
        question_router=QuestionRouter(),
        citation_assembler=CitationAssembler(),
        telemetry=TelemetryCollector(window_size=settings.telemetry_window_size),
    )
    queries = [
        ("What is revenue in 2024 for Acme?", "Acme", None),
        ("Какая выручка за 2024 у Beta?", "Beta", None),
        ("What does management commentary mention for Acme?", "Acme", "pdf"),
    ]
    qa_outputs = []
    audit_store = AuditStore(Path(settings.audit_db_file))
    for question, company, doc_type in queries:
        response = qa_service.answer(question, company=company, doc_type=doc_type)
        payload = response.model_dump()
        qa_outputs.append(
            {
                "question": question,
                "company": company,
                "doc_type": doc_type,
                "response": payload,
            }
        )
        audit_store.record_qa_run(
            created_at=IngestionReportStore.now_iso(),
            question=question,
            company=company,
            doc_type=doc_type,
            answer=response.answer,
            response_time_ms=response.response_time_ms,
            query_mode=response.query_mode,
            confidence=response.answer_confidence,
            source_count=len(response.relevant_chunks),
            payload=payload,
        )

    report_payload = report_store.load()
    audit_store.record_ingestion_run(
        created_at=ingestion_result.pipeline_report.finished_at,
        payload=report_payload if isinstance(report_payload, dict) else {},
    )

    controlled_report = {
        "dataset_path": str(dataset_path.resolve()),
        "index_directory": str(index_directory.resolve()),
        "ingestion": {
            "processed_files": ingestion_result.processed_files,
            "skipped_files": ingestion_result.skipped_files,
            "failed_files": len(ingestion_result.failed_files),
            "text_chunks": len(ingestion_result.text_chunks),
            "table_chunks": len(ingestion_result.table_chunks),
        },
        "ingestion_report": report_payload,
        "qa_outputs": qa_outputs,
        "retrieval_stats": retriever.stats(),
    }
    output_path = Path("storage/controlled_run_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(controlled_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(controlled_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
