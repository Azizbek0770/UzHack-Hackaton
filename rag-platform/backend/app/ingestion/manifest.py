from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from app.core.logger import get_logger


@dataclass
class ManifestRecord:
    """State for a previously ingested file."""

    content_hash: str
    last_modified: float
    size_bytes: int


class IngestionManifest:
    """Persistent manifest for incremental ingestion decisions."""

    def __init__(self, manifest_path: Path) -> None:
        self._manifest_path = manifest_path
        self._records: Dict[str, ManifestRecord] = {}
        self._logger = get_logger("ingestion_manifest")
        self._load()

    def should_ingest(self, file_path: Path) -> bool:
        """Determine whether file needs reprocessing."""

        key = str(file_path.resolve())
        existing = self._records.get(key)
        try:
            stats = file_path.stat()
        except OSError as exc:
            self._logger.warning("Cannot stat file=%s error=%s", file_path, exc)
            return False
        if existing is None:
            return True
        if existing.last_modified != stats.st_mtime or existing.size_bytes != stats.st_size:
            current_hash = self._hash_file(file_path)
            return current_hash != existing.content_hash
        return False

    def mark_ingested(self, file_path: Path) -> None:
        """Update manifest entry after successful processing."""

        try:
            stats = file_path.stat()
            self._records[str(file_path.resolve())] = ManifestRecord(
                content_hash=self._hash_file(file_path),
                last_modified=stats.st_mtime,
                size_bytes=stats.st_size,
            )
        except OSError as exc:
            self._logger.warning("Cannot update manifest for file=%s error=%s", file_path, exc)

    def save(self) -> None:
        """Persist manifest to disk."""

        self._manifest_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            key: {
                "content_hash": value.content_hash,
                "last_modified": value.last_modified,
                "size_bytes": value.size_bytes,
            }
            for key, value in self._records.items()
        }
        self._manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        """Load manifest state from disk if present."""

        if not self._manifest_path.exists():
            self._records = {}
            return
        try:
            data = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._logger.warning("Manifest load failed path=%s error=%s", self._manifest_path, exc)
            self._records = {}
            return
        self._records = {
            key: ManifestRecord(
                content_hash=str(value.get("content_hash", "")),
                last_modified=float(value.get("last_modified", 0.0)),
                size_bytes=int(value.get("size_bytes", 0)),
            )
            for key, value in data.items()
        }

    @staticmethod
    def _hash_file(file_path: Path) -> str:
        """Build deterministic hash from file bytes."""

        digest = hashlib.sha256()
        with file_path.open("rb") as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()
