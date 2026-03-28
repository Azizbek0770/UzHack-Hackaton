from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from app.chunking.semantic_chunker import SemanticChunker
from app.core.errors import DocumentProcessingError
from app.core.logger import get_logger
from app.ingestion.manifest import IngestionManifest
from app.ingestion.reporting import (
    IngestionFileReport,
    IngestionPipelineReport,
    IngestionReportStore,
)
from app.models.schemas import DocumentChunk, TableChunk
from app.parsing.json_parser import JsonParser
from app.parsing.pdf_parser import PdfParser
from app.parsing.xlsx_parser import XlsxParser
from app.retrieval.hybrid import HybridRetriever


@dataclass
class IngestionResult:
    """Output of ingestion pipeline."""

    text_chunks: List[DocumentChunk]
    table_chunks: List[TableChunk]
    processed_files: int
    skipped_files: int
    failed_files: List[str]
    pipeline_report: IngestionPipelineReport


class DocumentIngestor:
    """Traverse dataset and parse files into chunks."""

    def __init__(
        self,
        chunker: SemanticChunker,
        retriever: HybridRetriever,
        pdf_parser: PdfParser | None = None,
        xlsx_parser: XlsxParser | None = None,
        json_parser: JsonParser | None = None,
        manifest: Optional[IngestionManifest] = None,
        incremental: bool = True,
        report_store: Optional[IngestionReportStore] = None,
    ) -> None:
        self._chunker = chunker
        self._retriever = retriever
        self._pdf_parser = pdf_parser or PdfParser()
        self._xlsx_parser = xlsx_parser or XlsxParser()
        self._json_parser = json_parser or JsonParser()
        self._manifest = manifest
        self._incremental = incremental
        self._report_store = report_store
        self._logger = get_logger("ingestor")

    def ingest(self, dataset_path: Path) -> IngestionResult:
        """Ingest all files inside the dataset path."""

        text_chunks: List[DocumentChunk] = []
        table_chunks: List[TableChunk] = []
        processed_files = 0
        skipped_files = 0
        failed_files: List[str] = []
        file_reports: List[IngestionFileReport] = []
        started_at = IngestionReportStore.now_iso()
        for file_path in self._iter_files(dataset_path):
            if self._incremental and self._manifest and not self._manifest.should_ingest(file_path):
                skipped_files += 1
                self._logger.info("Skipped unchanged file=%s", file_path.name)
                file_reports.append(
                    IngestionFileReport(
                        file_path=str(file_path),
                        company=self._extract_company(dataset_path, file_path),
                        file_type=file_path.suffix.lower().replace(".", ""),
                        parser_status="skipped",
                        chunk_status="skipped",
                        index_status="skipped",
                    )
                )
                continue
            company = self._extract_company(dataset_path, file_path)
            report = IngestionFileReport(
                file_path=str(file_path),
                company=company,
                file_type=file_path.suffix.lower().replace(".", ""),
                parser_status="pending",
                chunk_status="pending",
                index_status="pending",
            )
            try:
                self._logger.info("Processing file=%s company=%s", file_path.name, company)
                if file_path.suffix.lower() == ".pdf":
                    chunks = self._pdf_parser.parse(file_path, company)
                    report.parser_status = "success"
                    chunked = self._chunker.chunk(chunks)
                    validated = self._validated_text_chunks(chunked)
                    report.chunk_status = "success"
                    report.text_chunks = len(validated)
                    text_chunks.extend(validated)
                elif file_path.suffix.lower() in {".xlsx", ".xls"}:
                    parsed = self._xlsx_parser.parse(file_path, company)
                    report.parser_status = "success"
                    validated = self._validated_table_chunks(parsed)
                    report.chunk_status = "success"
                    report.table_chunks = len(validated)
                    table_chunks.extend(validated)
                elif file_path.suffix.lower() == ".json":
                    chunks = self._json_parser.parse(file_path, company)
                    report.parser_status = "success"
                    chunked = self._chunker.chunk(chunks)
                    validated = self._validated_text_chunks(chunked)
                    report.chunk_status = "success"
                    report.text_chunks = len(validated)
                    text_chunks.extend(validated)
                if self._manifest:
                    self._manifest.mark_ingested(file_path)
                processed_files += 1
                report.index_status = "queued"
            except Exception as exc:
                failed_files.append(str(file_path))
                report.parser_status = "failed"
                report.chunk_status = "failed"
                report.index_status = "failed"
                report.error = str(exc)
                self._logger.error("Failed to parse file=%s error=%s", file_path, exc)
            file_reports.append(report)
        try:
            self._retriever.add_text_chunks(text_chunks)
            self._retriever.add_table_chunks(table_chunks)
        except Exception as exc:
            raise DocumentProcessingError(f"Indexing stage failed: {exc}") from exc
        for report in file_reports:
            if report.index_status == "queued":
                report.index_status = "indexed"
        if self._manifest:
            self._manifest.save()
        self._logger.info(
            "Ingestion complete. Text chunks=%s, Table chunks=%s, processed=%s, skipped=%s, failed=%s",
            len(text_chunks),
            len(table_chunks),
            processed_files,
            skipped_files,
            len(failed_files),
        )
        if not processed_files and failed_files:
            raise DocumentProcessingError("All files failed during ingestion.")
        pipeline_report = IngestionPipelineReport(
            started_at=started_at,
            finished_at=IngestionReportStore.now_iso(),
            processed_files=processed_files,
            skipped_files=skipped_files,
            failed_files=len(failed_files),
            text_chunks=len(text_chunks),
            table_chunks=len(table_chunks),
            files=file_reports,
        )
        if self._report_store:
            self._report_store.save(pipeline_report)
        return IngestionResult(
            text_chunks=text_chunks,
            table_chunks=table_chunks,
            processed_files=processed_files,
            skipped_files=skipped_files,
            failed_files=failed_files,
            pipeline_report=pipeline_report,
        )

    @staticmethod
    def _iter_files(dataset_path: Path) -> Iterable[Path]:
        """Iterate over supported files in dataset."""

        for file_path in sorted(dataset_path.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in {
                ".pdf",
                ".xlsx",
                ".xls",
                ".json",
            }:
                yield file_path

    @staticmethod
    def _extract_company(dataset_path: Path, file_path: Path) -> str:
        """Extract company name from dataset-relative path."""

        try:
            relative_parts = file_path.relative_to(dataset_path).parts
        except ValueError:
            return file_path.parent.name
        if not relative_parts:
            return file_path.parent.name
        if len(relative_parts) == 1:
            return file_path.parent.name
        return relative_parts[0]

    def _validated_text_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Validate text chunks for metadata and content integrity."""

        validated: List[DocumentChunk] = []
        for chunk in chunks:
            if not chunk.content.strip():
                continue
            if not chunk.metadata.file_name or chunk.page_index < 0:
                continue
            validated.append(chunk)
        return validated

    def _validated_table_chunks(self, chunks: List[TableChunk]) -> List[TableChunk]:
        """Validate table chunks for metadata and content integrity."""

        validated: List[TableChunk] = []
        for chunk in chunks:
            rows = chunk.content.get("rows", [])
            if not rows:
                continue
            if not chunk.metadata.file_name or chunk.sheet_index < 0:
                continue
            validated.append(chunk)
        return validated
