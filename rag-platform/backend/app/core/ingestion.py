"""
Document Ingestion Engine
Traverses the dataset directory, routes files to parsers,
and returns all chunks ready for embedding.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

import structlog

from app.core.config import settings
from app.core.logging import TimingLogger
from app.models.schemas import (
    DocType,
    DocumentChunk,
    DocumentMetadata,
    IngestionResult,
    Language,
    TableChunk,
)
from app.parsers.base import BaseParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.xlsx_parser import XLSXParser
from app.parsers.base import JSONParser

logger = structlog.get_logger(__name__)

# All supported parsers, tried in order
PARSERS: List[BaseParser] = [PDFParser(), XLSXParser(), JSONParser()]

# Folders/files to skip
SKIP_PATTERNS = {".DS_Store", "__MACOSX", "Thumbs.db", ".git"}

# Doc type heuristics based on filename keywords
DOC_TYPE_HINTS = {
    DocType.FINANCIAL_REPORT: ["финансов", "financial", "отчет", "report", "moliya"],
    DocType.ANNUAL_REPORT: ["годов", "annual", "yillik"],
    DocType.DISCLOSURE: ["раскрыт", "disclosure", "oshkor"],
    DocType.METADATA: ["metadata", "meta", "info"],
}


class IngestionEngine:
    """
    Traverses dataset directory, parses documents, and returns all chunks.

    Directory convention:
        dataset/
            {company_name}/
                {any_depth}/
                    *.pdf | *.xlsx | *.json
    """

    def __init__(self, dataset_dir: Optional[Path] = None):
        self.dataset_dir = dataset_dir or settings.DATASET_DIR

    def ingest_all(self) -> Tuple[List[DocumentChunk | TableChunk], IngestionResult]:
        """
        Ingest all documents in the dataset directory.

        Returns:
            (all_chunks, result_summary)
        """
        start = time.perf_counter()
        result = IngestionResult()
        all_chunks: List[DocumentChunk | TableChunk] = []

        if not self.dataset_dir.exists():
            logger.warning(
                "Dataset directory not found",
                path=str(self.dataset_dir),
            )
            return all_chunks, result

        files = self._discover_files()
        result.total_files = len(files)
        logger.info("Starting ingestion", total_files=len(files))

        for file_path in files:
            try:
                with TimingLogger("parse_file", logger, file=file_path.name):
                    chunks = self._ingest_file(file_path)

                all_chunks.extend(chunks)
                result.successful += 1

                # Count by type
                for c in chunks:
                    if hasattr(c, "raw_data"):  # TableChunk
                        result.total_table_chunks += 1
                    else:
                        result.total_text_chunks += 1

            except Exception as e:
                result.failed += 1
                result.errors.append({"file": str(file_path), "error": str(e)})
                logger.error(
                    "Ingestion failed for file",
                    file=str(file_path),
                    error=str(e),
                )

        result.duration_seconds = round(time.perf_counter() - start, 2)
        logger.info(
            "Ingestion complete",
            successful=result.successful,
            failed=result.failed,
            text_chunks=result.total_text_chunks,
            table_chunks=result.total_table_chunks,
            duration_s=result.duration_seconds,
        )
        return all_chunks, result

    def _discover_files(self) -> List[Path]:
        """Recursively discover all parseable files in the dataset directory."""
        files = []
        supported_extensions = {".pdf", ".xlsx", ".xls", ".xlsm", ".json"}

        for path in self.dataset_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in supported_extensions:
                if not any(skip in path.parts for skip in SKIP_PATTERNS):
                    files.append(path)

        return sorted(files)

    def _ingest_file(
        self, file_path: Path
    ) -> List[DocumentChunk | TableChunk]:
        """Route a single file to the appropriate parser."""
        metadata = self._build_metadata(file_path)

        for parser in PARSERS:
            if parser.can_parse(file_path):
                return parser.parse(file_path, metadata)

        logger.warning("No parser found for file", file=str(file_path))
        return []

    def _build_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Construct DocumentMetadata from file path.
        Company is inferred from the top-level folder under dataset/.
        """
        # Extract company: first folder below dataset_dir
        try:
            relative = file_path.relative_to(self.dataset_dir)
            company = relative.parts[0] if len(relative.parts) > 1 else "unknown"
        except ValueError:
            company = "unknown"

        doc_type = self._detect_doc_type(file_path.name)
        year = self._extract_year(file_path.name)

        return DocumentMetadata(
            company=company,
            file_name=file_path.name,
            file_path=str(file_path),
            doc_type=doc_type,
            language=Language.UNKNOWN,  # detected per-page during parsing
            year=year,
        )

    def _detect_doc_type(self, filename: str) -> DocType:
        """Heuristic doc type detection from filename."""
        lower = filename.lower()
        for doc_type, hints in DOC_TYPE_HINTS.items():
            if any(hint in lower for hint in hints):
                return doc_type
        return DocType.UNKNOWN

    def _extract_year(self, filename: str) -> Optional[int]:
        """Extract fiscal year from filename using regex."""
        import re
        match = re.search(r"(20\d{2})", filename)
        return int(match.group(1)) if match else None
