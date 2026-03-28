from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.chunking.semantic_chunker import SemanticChunker
from app.core.audit_db import AuditStore
from app.core.cache import InMemoryCache
from app.core.config import RetrievalSettings, get_settings
from app.core.container import get_audit_store, get_qa_service, get_retriever, get_telemetry
from app.core.telemetry import TelemetryCollector
from app.ingestion.ingestor import DocumentIngestor
from app.ingestion.manifest import IngestionManifest
from app.ingestion.reporting import IngestionReportStore
from app.main import create_app
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


def _ensure_company_corpus(dataset_path: Path, company: str, year: int, revenue: int, profit: int) -> None:
    company_dir = dataset_path / company
    company_dir.mkdir(parents=True, exist_ok=True)
    if fitz is not None:
        pdf_path = company_dir / "annual_report.pdf"
        document = fitz.open()
        page1 = document.new_page()
        page1.insert_text(
            (72, 72),
            f"{company} management commentary for {year}. Strategy improved operational resilience.",
        )
        page2 = document.new_page()
        page2.insert_text((72, 72), f"Выручка за {year} год усилилась благодаря инвестициям.")
        page3 = document.new_page()
        page3.insert_text((72, 72), f"{year} yilda daromad va foyda barqaror o'sdi.")
        document.save(str(pdf_path))
        document.close()
    pd.DataFrame(
        {
            "Metric": ["Revenue", "Profit", "Assets"],
            str(year): [str(revenue), str(profit), str(revenue * 2)],
        }
    ).to_excel(company_dir / "financials.xlsx", index=False)
    (company_dir / "company.json").write_text(
        json.dumps(
            {
                "company": company,
                "country": "Uzbekistan",
                "year": year,
                "sector": "Finance",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _ensure_external_dataset(dataset_path: Path) -> None:
    dataset_path.mkdir(parents=True, exist_ok=True)
    has_supported = any(
        path.suffix.lower() in {".pdf", ".xlsx", ".xls", ".json"}
        for path in dataset_path.rglob("*")
        if path.is_file()
    )
    if has_supported:
        return
    _ensure_company_corpus(dataset_path, "Orion", 2024, 1820, 410)
    _ensure_company_corpus(dataset_path, "SamarkandCapital", 2024, 1340, 290)
    _ensure_company_corpus(dataset_path, "TashkentHoldings", 2024, 2150, 530)


def run() -> None:
    settings = get_settings()
    external_path = os.getenv(
        "RAG_EXTERNAL_DATASET_PATH",
        str(Path(settings.controlled_dataset_path).resolve().parents[1] / "external_dataset"),
    )
    dataset_path = Path(external_path)
    _ensure_external_dataset(dataset_path)

    retriever = HybridRetriever(
        text_store=FaissStore(DummyEmbedder()),
        table_store=FaissStore(DummyEmbedder()),
        bm25_store=BM25Store(),
        settings=RetrievalSettings(text_top_k=8, table_top_k=8),
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
    retriever.save(Path(settings.index_directory))

    telemetry = TelemetryCollector(window_size=settings.telemetry_window_size)
    qa_service = QAService(
        retriever=retriever,
        table_qa=TableQAEngine(),
        llm_client=LLMClient(endpoint=None, api_key=None),
        cache=InMemoryCache(ttl_seconds=settings.cache_ttl_seconds),
        question_router=QuestionRouter(),
        citation_assembler=CitationAssembler(),
        telemetry=telemetry,
    )
    audit_store = AuditStore(Path(settings.audit_db_file))
    audit_store.record_ingestion_run(
        created_at=ingestion_result.pipeline_report.finished_at,
        payload=report_store.load(),
    )

    benchmark_queries = [
        {"question": "What is revenue in 2024 for Orion?", "company": "Orion", "expected": "financials.xlsx"},
        {"question": "Какая выручка за 2024 у SamarkandCapital?", "company": "SamarkandCapital", "expected": "financials.xlsx"},
        {"question": "2024 daromad qancha TashkentHoldings?", "company": "TashkentHoldings", "expected": "financials.xlsx"},
        {"question": "What does management commentary mention for Orion?", "company": "Orion", "expected": "annual_report.pdf"},
    ]
    hits = 0
    qa_records = []
    for item in benchmark_queries:
        response = qa_service.answer(item["question"], company=item["company"])
        payload = response.model_dump()
        files = [source["file"] for source in payload["relevant_chunks"]]
        is_hit = item["expected"] in files
        hits += 1 if is_hit else 0
        qa_records.append(
            {
                "question": item["question"],
                "company": item["company"],
                "expected_file": item["expected"],
                "hit": is_hit,
                "response": payload,
            }
        )
        audit_store.record_qa_run(
            created_at=IngestionReportStore.now_iso(),
            question=item["question"],
            company=item["company"],
            doc_type=None,
            answer=response.answer,
            response_time_ms=response.response_time_ms,
            query_mode=response.query_mode,
            confidence=response.answer_confidence,
            source_count=len(response.relevant_chunks),
            payload=payload,
        )
    hit_rate = hits / len(benchmark_queries)

    app = create_app()
    app.dependency_overrides[get_retriever] = lambda: retriever
    app.dependency_overrides[get_qa_service] = lambda: qa_service
    app.dependency_overrides[get_telemetry] = lambda: telemetry
    app.dependency_overrides[get_audit_store] = lambda: audit_store

    with TestClient(app) as client:
        endpoint_snapshots = {
            "/health": client.get("/health").json(),
            "/metrics": client.get("/metrics").json(),
            "/ingestion/report": client.get("/ingestion/report").json(),
            "/audit/runs": client.get("/audit/runs").json(),
        }

    output = {
        "dataset_path": str(dataset_path.resolve()),
        "index_directory": str(Path(settings.index_directory).resolve()),
        "benchmark": {
            "queries": qa_records,
            "hit_rate": round(hit_rate, 4),
            "query_count": len(benchmark_queries),
        },
        "ingestion": {
            "processed_files": ingestion_result.processed_files,
            "skipped_files": ingestion_result.skipped_files,
            "failed_files": len(ingestion_result.failed_files),
            "text_chunks": len(ingestion_result.text_chunks),
            "table_chunks": len(ingestion_result.table_chunks),
        },
        "endpoint_snapshots": endpoint_snapshots,
    }
    output_path = Path("storage/external_corpus_benchmark_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
