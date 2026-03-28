from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.models.schemas import Metadata, TableChunk
from app.tables.table_qa import TableQAEngine


def test_table_qa_engine_answers_metric() -> None:
    """Table QA extracts numeric metric."""

    metadata = Metadata(company="Acme", doc_type="xlsx", file_name="report.xlsx")
    table = TableChunk(
        content={
            "sheet_name": "Sheet1",
            "columns": ["Metric", "2023"],
            "rows": [{"Metric": "Revenue", "2023": "1000"}],
        },
        sheet_index=0,
        metadata=metadata,
    )
    engine = TableQAEngine()
    answer = engine.answer("What is the revenue in 2023?", [table])
    assert answer is not None
    assert "1000" in answer.answer
