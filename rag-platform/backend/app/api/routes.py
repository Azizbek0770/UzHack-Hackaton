from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.chunking.semantic_chunker import SemanticChunker
from app.core.audit_db import AuditStore
from app.core.container import (
    get_audit_store,
    get_cache,
    get_qa_service,
    get_retriever,
    get_telemetry,
)
from app.core.config import get_settings
from app.core.errors import QAError
from app.core.telemetry import TelemetryCollector
from app.core.cache import InMemoryCache
from app.ingestion.ingestor import DocumentIngestor
from app.ingestion.manifest import IngestionManifest
from app.ingestion.reporting import IngestionReportStore
from app.models.schemas import QueryRequest, QueryResponse
from app.parsing.pdf_parser import PdfParser, PdfParserConfig
from app.qa.service import QAService
from app.retrieval.hybrid import HybridRetriever

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_endpoint(
    payload: QueryRequest,
    qa_service: QAService = Depends(get_qa_service),
    audit_store: AuditStore = Depends(get_audit_store),
) -> QueryResponse:
    """Answer a query using the QA service."""

    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="Question must not be empty.")
    try:
        response = qa_service.answer(
            payload.question,
            company=payload.company,
            doc_type=payload.doc_type,
        )
        audit_store.record_qa_run(
            created_at=datetime.now(timezone.utc).isoformat(),
            question=payload.question,
            company=payload.company,
            doc_type=payload.doc_type,
            answer=response.answer,
            response_time_ms=response.response_time_ms,
            query_mode=response.query_mode,
            confidence=response.answer_confidence,
            source_count=len(response.relevant_chunks),
            payload=response.model_dump(),
        )
        return response
    except QAError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal QA pipeline error.") from exc


@router.get("/metrics")
def metrics_endpoint(
    telemetry: TelemetryCollector = Depends(get_telemetry),
) -> dict:
    """Return aggregated runtime metrics for QA operations."""

    return telemetry.summary()


@router.get("/health")
def health_endpoint(
    retriever: HybridRetriever = Depends(get_retriever),
    telemetry: TelemetryCollector = Depends(get_telemetry),
) -> dict:
    """Return lightweight service health and index readiness."""

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retrieval": retriever.stats(),
        "metrics": telemetry.summary(),
    }


@router.get("/ingestion/report")
def ingestion_report_endpoint() -> dict:
    """Return latest per-stage ingestion report with failed file details."""

    settings = get_settings()
    report_store = IngestionReportStore(Path(settings.ingestion_report_file))
    return report_store.load()


@router.get("/audit/runs")
def audit_runs_endpoint(
    audit_store: AuditStore = Depends(get_audit_store),
) -> dict:
    """Return latest ingestion and QA audit records."""

    return audit_store.latest_runs(limit=20)


@router.post("/ingestion/upload")
async def upload_ingestion_endpoint(
    company: str = Form(...),
    files: list[UploadFile] = File(...),
    retriever: HybridRetriever = Depends(get_retriever),
    audit_store: AuditStore = Depends(get_audit_store),
    cache: InMemoryCache = Depends(get_cache),
) -> dict:
    settings = get_settings()
    normalized_company = company.strip()
    if not normalized_company:
        raise HTTPException(status_code=422, detail="Company must not be empty.")
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required.")
    allowed_extensions = {".pdf", ".xlsx", ".xls", ".json"}
    batch_id = uuid.uuid4().hex[:10]
    batch_root = Path(settings.controlled_dataset_path) / "upload_batches" / batch_id
    company_dir = batch_root / normalized_company
    company_dir.mkdir(parents=True, exist_ok=True)
    saved_files: list[str] = []
    skipped_files: list[str] = []
    for file in files:
        extension = Path(file.filename or "").suffix.lower()
        if extension not in allowed_extensions:
            skipped_files.append(file.filename or "unknown")
            continue
        destination = company_dir / Path(file.filename).name
        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        saved_files.append(str(destination))
    if not saved_files:
        raise HTTPException(status_code=422, detail="No supported files uploaded.")
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
    result = ingestor.ingest(batch_root)
    retriever.save(Path(settings.index_directory))
    report_payload = report_store.load()
    audit_store.record_ingestion_run(
        created_at=result.pipeline_report.finished_at,
        payload=report_payload if isinstance(report_payload, dict) else {},
    )
    cache.clear()
    return {
        "company": normalized_company,
        "batch_id": batch_id,
        "saved_files": saved_files,
        "skipped_files": skipped_files,
        "processed_files": result.processed_files,
        "failed_files": len(result.failed_files),
        "text_chunks": len(result.text_chunks),
        "table_chunks": len(result.table_chunks),
        "report": report_payload,
    }


@router.get("/ingestion/uploads")
def list_uploaded_batches_endpoint() -> dict:
    settings = get_settings()
    base_path = Path(settings.controlled_dataset_path) / "upload_batches"
    if not base_path.exists():
        return {"batches": []}
    batches = []
    for batch_dir in sorted(base_path.iterdir(), reverse=True):
        if not batch_dir.is_dir():
            continue
        files = [str(path) for path in batch_dir.rglob("*") if path.is_file()]
        batches.append(
            {
                "batch_id": batch_dir.name,
                "file_count": len(files),
                "files": files[:50],
            }
        )
    return {"batches": batches[:20]}
