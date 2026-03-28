from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.ingestion.manifest import IngestionManifest


def test_ingestion_manifest_tracks_file_state(tmp_path: Path) -> None:
    """Manifest persists file ingestion fingerprint and skips unchanged files."""

    manifest_path = tmp_path / "manifest.json"
    data_file = tmp_path / "sample.json"
    data_file.write_text('{"a": 1}', encoding="utf-8")
    manifest = IngestionManifest(manifest_path)
    assert manifest.should_ingest(data_file)
    manifest.mark_ingested(data_file)
    manifest.save()

    reloaded = IngestionManifest(manifest_path)
    assert not reloaded.should_ingest(data_file)

    data_file.write_text('{"a": 2}', encoding="utf-8")
    assert reloaded.should_ingest(data_file)
