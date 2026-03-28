from __future__ import annotations

from pathlib import Path

from app.chunking.semantic_chunker import SemanticChunker
from app.core.audit_db import AuditStore
from app.core.config import get_settings
from app.ingestion.ingestor import DocumentIngestor
from app.ingestion.manifest import IngestionManifest
from app.ingestion.reporting import IngestionReportStore
from app.parsing.pdf_parser import PdfParser, PdfParserConfig
from app.retrieval.hybrid import HybridRetriever
from app.core.container import get_retriever


def run() -> None:
    """Ingest dataset and build indexes."""

    settings = get_settings()
    dataset_path = Path(settings.dataset_path)
    retriever: HybridRetriever = get_retriever()
    if not settings.enable_incremental_ingestion:
        retriever.reset()
    manifest = IngestionManifest(Path(settings.ingestion_manifest_file))
    report_store = IngestionReportStore(Path(settings.ingestion_report_file))
    audit_store = AuditStore(Path(settings.audit_db_file))
    pdf_parser = PdfParser(
        PdfParserConfig(
            enable_ocr=settings.ocr_enabled,
            ocr_language_mode=settings.ocr_language_mode,
            ocr_min_confidence=settings.ocr_min_confidence,
        )
    )
    ingestor = DocumentIngestor(
        chunker=SemanticChunker(),
        retriever=retriever,
        pdf_parser=pdf_parser,
        manifest=manifest,
        incremental=settings.enable_incremental_ingestion,
        report_store=report_store,
    )
    result = ingestor.ingest(dataset_path)
    retriever.save(Path(settings.index_directory))
    audit_store.record_ingestion_run(
        created_at=result.pipeline_report.finished_at,
        payload=report_store.load(),
    )
    print(
        f"Processed files: {result.processed_files}, skipped files: {result.skipped_files}, "
        f"failed files: {len(result.failed_files)}, text chunks: {len(result.text_chunks)}, "
        f"table chunks: {len(result.table_chunks)}"
    )


if __name__ == "__main__":
    run()
