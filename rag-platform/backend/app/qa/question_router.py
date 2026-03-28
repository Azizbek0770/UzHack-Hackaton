from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class QuestionAnalysis:
    """Structured analysis of user question intent."""

    mode: Literal["table", "text", "hybrid"]
    has_numeric_intent: bool
    has_table_intent: bool
    detected_year: str | None


class QuestionRouter:
    """Detect query intent to route retrieval and QA path."""

    _table_keywords = (
        "revenue",
        "profit",
        "ebitda",
        "assets",
        "liabilities",
        "balance sheet",
        "income statement",
        "выручка",
        "прибыль",
        "активы",
        "обязательства",
        "daromad",
        "foyda",
        "aktivlar",
        "majburiyatlar",
    )

    _text_keywords = (
        "risk",
        "strategy",
        "management",
        "guidance",
        "commentary",
        "опис",
        "стратег",
        "izoh",
        "tavsif",
    )

    def analyze(self, question: str) -> QuestionAnalysis:
        """Analyze question and classify best QA mode."""

        lower = question.lower()
        has_year = bool(re.search(r"(19|20)\d{2}", lower))
        has_digit = any(char.isdigit() for char in lower)
        has_currency = any(token in lower for token in ("$", "usd", "sum", "сум", "млрд", "mlrd"))
        has_table_intent = any(keyword in lower for keyword in self._table_keywords) or has_year
        has_text_intent = any(keyword in lower for keyword in self._text_keywords)
        has_numeric_intent = has_digit or has_currency or has_table_intent
        if has_table_intent and has_text_intent:
            mode: Literal["table", "text", "hybrid"] = "hybrid"
        elif has_table_intent or has_numeric_intent:
            mode = "table"
        else:
            mode = "text"
        detected_year = self._extract_year(lower)
        return QuestionAnalysis(
            mode=mode,
            has_numeric_intent=has_numeric_intent,
            has_table_intent=has_table_intent,
            detected_year=detected_year,
        )

    @staticmethod
    def _extract_year(question: str) -> str | None:
        """Extract a 4-digit year from a question."""

        match = re.search(r"(19|20)\d{2}", question)
        return match.group(0) if match else None
