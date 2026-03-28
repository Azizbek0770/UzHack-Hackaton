from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.api.routes import router
from app.core.audit_db import AuditStore
from app.core.container import get_audit_store, get_retriever
from app.core.config import get_settings


class DummyRetriever:
    def __init__(self) -> None:
        self.text = []
        self.tables = []

    def add_text_chunks(self, chunks):
        self.text.extend(chunks)

    def add_table_chunks(self, chunks):
        self.tables.extend(chunks)

    def save(self, storage_dir):
        Path(storage_dir).mkdir(parents=True, exist_ok=True)

    def stats(self):
        return {"text_chunks": len(self.text), "table_chunks": len(self.tables), "bm25_chunks": len(self.text) + len(self.tables)}


def test_upload_ingestion_endpoint_accepts_json(tmp_path: Path) -> None:
    os.environ["RAG_CONTROLLED_DATASET_PATH"] = str(tmp_path / "dataset")
    os.environ["RAG_INGESTION_REPORT_FILE"] = str(tmp_path / "ingestion_report.json")
    os.environ["RAG_INGESTION_MANIFEST_FILE"] = str(tmp_path / "manifest.json")
    os.environ["RAG_INDEX_DIRECTORY"] = str(tmp_path / "indexes")
    os.environ["RAG_AUDIT_DB_FILE"] = str(tmp_path / "audit.sqlite3")
    get_settings.cache_clear()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_retriever] = lambda: DummyRetriever()
    app.dependency_overrides[get_audit_store] = lambda: AuditStore(tmp_path / "audit.sqlite3")

    with TestClient(app) as client:
        response = client.post(
            "/ingestion/upload",
            data={"company": "UploadCo"},
            files={"files": ("meta.json", b'{"company":"UploadCo","year":2024}', "application/json")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["processed_files"] >= 1
        assert payload["failed_files"] == 0
