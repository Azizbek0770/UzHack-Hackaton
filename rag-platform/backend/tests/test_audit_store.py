from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.audit_db import AuditStore


def test_audit_store_records_ingestion_and_qa_runs(tmp_path: Path) -> None:
    """Audit store persists and returns recent run records."""

    store = AuditStore(tmp_path / "audit.sqlite3")
    store.record_ingestion_run(
        created_at="2026-01-01T00:00:00Z",
        payload={"processed_files": 2, "failed_files": 0},
    )
    store.record_qa_run(
        created_at="2026-01-01T00:01:00Z",
        question="What is revenue?",
        company="Acme",
        doc_type=None,
        answer="Revenue is 100",
        response_time_ms=14,
        query_mode="table",
        confidence=0.9,
        source_count=1,
        payload={"answer": "Revenue is 100"},
    )
    data = store.latest_runs(limit=5)
    assert len(data["ingestion_runs"]) == 1
    assert len(data["qa_runs"]) == 1
    assert data["qa_runs"][0]["question"] == "What is revenue?"
