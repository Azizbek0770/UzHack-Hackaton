from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.models.schemas import SourceRef, TableChunk
from app.tables.semantics import TableSemanticsResolver


@dataclass
class TableAnswer:
    """Answer extracted from table data."""

    answer: str
    sources: List[SourceRef]


class TableQAEngine:
    """Extract numeric answers directly from table chunks."""

    def __init__(self) -> None:
        self._resolver = TableSemanticsResolver()

    def answer(self, question: str, tables: List[TableChunk]) -> Optional[TableAnswer]:
        """Try to answer a question purely from tables."""

        match = self._resolver.resolve(question, tables)
        if not match:
            return None
        source = SourceRef(
            file=match.file_name,
            page=match.sheet_index,
            company=match.company,
            doc_type="xlsx",
            score=round(match.score, 4),
        )
        period_suffix = f" for {match.period}" if match.period else ""
        return TableAnswer(
            answer=f"{match.metric.capitalize()} is {match.value}{period_suffix} based on table data.",
            sources=[source],
        )
