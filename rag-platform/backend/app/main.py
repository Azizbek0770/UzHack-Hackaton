from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.chunking.semantic_chunker import SemanticChunker
from app.core.audit_db import AuditStore
from app.core.config import get_settings
from app.core.container import get_retriever
from app.core.logger import get_logger, setup_logging
from app.ingestion.ingestor import DocumentIngestor
from app.ingestion.manifest import IngestionManifest
from app.ingestion.reporting import IngestionReportStore
from app.parsing.pdf_parser import PdfParser, PdfParserConfig


def create_app() -> FastAPI:
    """Create FastAPI application."""

    settings = get_settings()
    setup_logging()
    logger = get_logger("startup")
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.include_router(router)

    @app.on_event("startup")
    async def ingest_on_startup() -> None:
        if not settings.ingest_on_startup:
            logger.info("Startup ingestion disabled.")
            return
        dataset_path = Path(settings.dataset_path)
        if not dataset_path.exists():
            logger.warning("Dataset path not found: %s", dataset_path)
            return
        retriever = get_retriever()
        if not settings.enable_incremental_ingestion:
            retriever.reset()
        pdf_parser = PdfParser(
            PdfParserConfig(
                enable_ocr=settings.ocr_enabled,
                ocr_language_mode=settings.ocr_language_mode,
                ocr_min_confidence=settings.ocr_min_confidence,
            )
        )
        manifest = IngestionManifest(Path(settings.ingestion_manifest_file))
        report_store = IngestionReportStore(Path(settings.ingestion_report_file))
        audit_store = AuditStore(Path(settings.audit_db_file))
        ingestor = DocumentIngestor(
            chunker=SemanticChunker(),
            retriever=retriever,
            pdf_parser=pdf_parser,
            manifest=manifest,
            incremental=settings.enable_incremental_ingestion,
            report_store=report_store,
        )
        ingestion_result = ingestor.ingest(dataset_path)
        retriever.save(Path(settings.index_directory))
        audit_store.record_ingestion_run(
            created_at=ingestion_result.pipeline_report.finished_at,
            payload=report_store.load(),
        )
        logger.info(
            "Startup ingestion done: processed=%s skipped=%s failed=%s",
            ingestion_result.processed_files,
            ingestion_result.skipped_files,
            len(ingestion_result.failed_files),
        )

    return app


app = create_app()
