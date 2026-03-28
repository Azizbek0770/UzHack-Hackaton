from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from app.models.schemas import TableChunk


@dataclass
class SemanticMatch:
    """Resolved table metric candidate."""

    metric: str
    value: str
    sheet_index: int
    file_name: str
    company: str
    score: float
    period: str | None


class TableSemanticsResolver:
    """Resolve metrics, units, and periods from mixed tabular inputs."""

    def __init__(self) -> None:
        self._metric_aliases: Dict[str, tuple[str, ...]] = {
            "revenue": ("revenue", "выручка", "daromad", "tushum"),
            "profit": ("profit", "прибыль", "foyda"),
            "assets": ("assets", "активы", "aktivlar"),
            "liabilities": ("liabilities", "обязательства", "majburiyatlar"),
            "ebitda": ("ebitda", "операционная прибыль", "operatsion foyda"),
        }

    def resolve(
        self,
        question: str,
        tables: Iterable[TableChunk],
    ) -> Optional[SemanticMatch]:
        """Find strongest metric match from all table chunks."""

        metric = self._detect_metric(question)
        if not metric:
            return None
        period = self._extract_period(question)
        matches: list[SemanticMatch] = []
        for table in tables:
            for row in table.content.get("rows", []):
                row_score = 0.0
                row_text = " ".join(str(value).lower() for value in row.values())
                if any(alias in row_text for alias in self._metric_aliases[metric]):
                    row_score += 1.0
                value = self._pick_value(row, metric=metric, period=period)
                if not value:
                    continue
                if period and period in row_text:
                    row_score += 1.0
                if row_score <= 0:
                    continue
                matches.append(
                    SemanticMatch(
                        metric=metric,
                        value=value,
                        sheet_index=table.sheet_index,
                        file_name=table.metadata.file_name,
                        company=table.metadata.company,
                        score=row_score,
                        period=period,
                    )
                )
        if not matches:
            return None
        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[0]

    def _detect_metric(self, question: str) -> str | None:
        lower = question.lower()
        for metric, aliases in self._metric_aliases.items():
            if any(alias in lower for alias in aliases):
                return metric
        return None

    @staticmethod
    def _extract_period(question: str) -> str | None:
        match = re.search(r"(19|20)\d{2}", question)
        return match.group(0) if match else None

    def _pick_value(self, row: dict, metric: str, period: str | None) -> str | None:
        if period:
            for key, value in row.items():
                if period in str(key) or period in str(value):
                    normalized = self._normalize_numeric(str(value))
                    if normalized:
                        return normalized
        aliases = self._metric_aliases[metric]
        for key, value in row.items():
            if any(alias in str(key).lower() for alias in aliases):
                normalized = self._normalize_numeric(str(value))
                if normalized:
                    return normalized
        for value in row.values():
            normalized = self._normalize_numeric(str(value))
            if normalized:
                return normalized
        return None

    @staticmethod
    def _normalize_numeric(raw: str) -> str | None:
        text = raw.strip().replace(" ", "")
        text = text.replace(",", ".")
        multiplier = 1.0
        lower = raw.lower()
        if "mlrd" in lower or "млрд" in lower:
            multiplier = 1_000_000_000.0
        if "mln" in lower or "млн" in lower:
            multiplier = 1_000_000.0
        number_only = re.sub(r"[^0-9.\-]", "", text)
        if not re.match(r"^-?\d+(\.\d+)?$", number_only):
            return None
        numeric = float(number_only) * multiplier
        if numeric.is_integer():
            return str(int(numeric))
        return f"{numeric:.4f}".rstrip("0").rstrip(".")
