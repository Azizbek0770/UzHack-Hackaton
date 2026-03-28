from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class AuditStore:
    """SQLite-backed audit store for ingestion and QA run records."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS qa_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                question TEXT NOT NULL,
                company TEXT,
                doc_type TEXT,
                answer TEXT NOT NULL,
                response_time_ms INTEGER,
                query_mode TEXT,
                confidence REAL,
                source_count INTEGER,
                payload_json TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def record_ingestion_run(self, created_at: str, payload: dict[str, Any]) -> None:
        """Persist one ingestion run payload."""

        self._connection.execute(
            "INSERT INTO ingestion_runs(created_at, payload_json) VALUES(?, ?)",
            (created_at, json.dumps(payload, ensure_ascii=False)),
        )
        self._connection.commit()

    def record_qa_run(
        self,
        *,
        created_at: str,
        question: str,
        company: str | None,
        doc_type: str | None,
        answer: str,
        response_time_ms: int | None,
        query_mode: str | None,
        confidence: float | None,
        source_count: int,
        payload: dict[str, Any],
    ) -> None:
        """Persist one QA query/response record."""

        self._connection.execute(
            """
            INSERT INTO qa_runs(
                created_at, question, company, doc_type, answer, response_time_ms,
                query_mode, confidence, source_count, payload_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                question,
                company,
                doc_type,
                answer,
                response_time_ms,
                query_mode,
                confidence,
                source_count,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        self._connection.commit()

    def latest_runs(self, limit: int = 10) -> dict[str, list[dict[str, Any]]]:
        """Return latest ingestion and QA runs for debugging."""

        ingestion_rows = self._connection.execute(
            "SELECT id, created_at, payload_json FROM ingestion_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        qa_rows = self._connection.execute(
            """
            SELECT id, created_at, question, company, doc_type, answer, response_time_ms,
                   query_mode, confidence, source_count, payload_json
            FROM qa_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return {
            "ingestion_runs": [
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "payload": json.loads(row["payload_json"]),
                }
                for row in ingestion_rows
            ],
            "qa_runs": [
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "question": row["question"],
                    "company": row["company"],
                    "doc_type": row["doc_type"],
                    "answer": row["answer"],
                    "response_time_ms": row["response_time_ms"],
                    "query_mode": row["query_mode"],
                    "confidence": row["confidence"],
                    "source_count": row["source_count"],
                    "payload": json.loads(row["payload_json"]),
                }
                for row in qa_rows
            ],
        }
