from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.logger import get_logger


@dataclass
class IngestionFileReport:
    """Per-file ingestion stage outcome."""

    file_path: str
    company: str
    file_type: str
    parser_status: str
    chunk_status: str
    index_status: str
    error: str | None = None
    text_chunks: int = 0
    table_chunks: int = 0


@dataclass
class IngestionPipelineReport:
    """Global ingestion pipeline report."""

    started_at: str
    finished_at: str
    processed_files: int
    skipped_files: int
    failed_files: int
    text_chunks: int
    table_chunks: int
    files: list[IngestionFileReport]


class IngestionReportStore:
    """Store and load ingestion reports from disk."""

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._logger = get_logger("ingestion_report")

    def save(self, report: IngestionPipelineReport) -> None:
        """Persist report payload."""

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(report)
        self._file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self) -> dict[str, Any]:
        """Load latest report payload."""

        if not self._file_path.exists():
            return {
                "status": "missing",
                "detail": "No ingestion report has been generated yet.",
            }
        try:
            return json.loads(self._file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._logger.warning("Failed to load ingestion report: %s", exc)
            return {"status": "corrupted", "detail": "Ingestion report file is not readable."}

    @staticmethod
    def now_iso() -> str:
        """Return UTC ISO timestamp."""

        return datetime.now(timezone.utc).isoformat()
