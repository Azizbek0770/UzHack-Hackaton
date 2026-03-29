"""
Query Understanding Layer
Classifies queries by type to route them to the correct QA strategy.
Rule-based with regex patterns for multilingual financial queries (Uzbek/Russian/English).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import structlog

from app.models.schemas import QueryType

logger = structlog.get_logger(__name__)


@dataclass
class QueryAnalysis:
    """Result of query analysis."""
    query_type: QueryType
    is_numeric: bool
    is_table_based: bool
    is_multi_hop: bool
    target_metric: Optional[str]  # e.g. "revenue", "profit"
    target_year: Optional[int]
    target_company: Optional[str]
    confidence: float  # classifier confidence


# ── Pattern dictionaries ──────────────────────────────────────────────────────

NUMERIC_PATTERNS = [
    # Russian
    r"сколько", r"какой объем", r"какова сумма", r"размер",
    r"величина", r"итого", r"всего", r"\d+.*год",
    # Uzbek — expanded
    r"qancha", r"necha", r"miqdor", r"hajmi", r"summasi",
    r"nechta", r"qanchaga", r"ulushi", r"qanday miqdor",
    r"ko'rsatkichi", r"qanday bo'lgan",
    # English
    r"how much", r"what is the", r"total", r"amount", r"how many",
]

TABLE_PATTERNS = [
    # Russian
    r"таблиц", r"показател", r"финансов", r"баланс",
    r"отчет", r"за\s+\d{4}", r"динамик", r"рост",
    # English
    r"table", r"balance", r"sheet", r"statement",
    # Uzbek — expanded
    r"jadval", r"ko'rsatkich", r"hisobot", r"moliyaviy",
    r"aktivlar", r"passivlar", r"kapital\b", r"foyda\b", r"zarar\b",
    r"daromad\b", r"tushum\b", r"xarajat\b",
]

MULTI_HOP_PATTERNS = [
    r"по сравнению", r"разница", r"изменени", r"рост.*по отношению",
    r"compared", r"difference", r"change.*from",
    r"solishtirgan", r"farqi", r"o'zgarishi", r"o'sishi",
]

METRIC_PATTERNS = {
    "revenue": [r"выручк", r"доход", r"revenue", r"daromad", r"tushum", r"реализация"],
    "profit": [r"прибыл", r"profit", r"foyda", r"sof foyda"],
    "assets": [r"актив", r"assets", r"aktivlar", r"баланс"],
    "liabilities": [r"обязательств", r"liabilities", r"majburiyat", r"passiv"],
    "equity": [r"капитал", r"equity", r"kapital", r"собственный"],
    "loss": [r"убыток", r"loss", r"zarar", r"sof zarar"],
    "employees": [r"сотрудник", r"работник", r"employees", r"xodim", r"ishchi"],
}


class QueryClassifier:
    """
    Rule-based query classifier for financial QA.

    Classifies into:
    - NUMERIC: expects a number answer
    - TEXTUAL: expects a prose answer
    - TABLE: needs table-based retrieval
    - MULTI_HOP: requires chaining facts

    Extracts:
    - target metric (revenue, profit, etc.)
    - target year
    - target company
    """

    def analyze(self, question: str) -> QueryAnalysis:
        """
        Analyze a question and return a QueryAnalysis.

        Args:
            question: Raw user question string.

        Returns:
            QueryAnalysis with type classification and extracted entities.
        """
        lower = question.lower()

        is_numeric = self._matches_any(lower, NUMERIC_PATTERNS)
        is_table = self._matches_any(lower, TABLE_PATTERNS)
        is_multi_hop = self._matches_any(lower, MULTI_HOP_PATTERNS)

        target_metric = self._extract_metric(lower)
        target_year = self._extract_year(question)
        target_company = self._extract_company(question)

        # Routing logic
        if is_multi_hop:
            query_type = QueryType.MULTI_HOP
            confidence = 0.80
        elif is_table or (is_numeric and target_metric):
            query_type = QueryType.TABLE
            confidence = 0.85
        elif is_numeric:
            query_type = QueryType.NUMERIC
            confidence = 0.75
        else:
            query_type = QueryType.TEXTUAL
            confidence = 0.70

        analysis = QueryAnalysis(
            query_type=query_type,
            is_numeric=is_numeric,
            is_table_based=is_table,
            is_multi_hop=is_multi_hop,
            target_metric=target_metric,
            target_year=target_year,
            target_company=target_company,
            confidence=confidence,
        )

        logger.debug(
            "Query analyzed",
            type=query_type.value,
            metric=target_metric,
            year=target_year,
            company=target_company,
        )
        return analysis

    def _matches_any(self, text: str, patterns: List[str]) -> bool:
        return any(re.search(p, text) for p in patterns)

    def _extract_metric(self, text: str) -> Optional[str]:
        for metric, patterns in METRIC_PATTERNS.items():
            if self._matches_any(text, patterns):
                return metric
        return None

    def _extract_year(self, text: str) -> Optional[int]:
        match = re.search(r"\b(20\d{2})\b", text)
        return int(match.group(1)) if match else None

    def _extract_company(self, text: str) -> Optional[str]:
        """
        Heuristic company extraction.
        Handles Uzbek AJ/ATB/MCHJ, Russian АО/ОАО, and quoted names.
        """
        # Standard quotes
        quoted = re.search(r'"([^"]{3,50})"', text)
        if quoted:
            return quoted.group(1).strip()

        # Cyrillic angle quotes «Company Name»
        cyrillic_quoted = re.search(r'«([^»]{3,50})»', text)
        if cyrillic_quoted:
            return cyrillic_quoted.group(1).strip()

        # Uzbek/Russian legal forms + company name
        legal_match = re.search(
            r'(?:АО|ОАО|ООО|ЗАО|АКБ|JSC|LLC|AJ|ATB|MCHJ|QK)\s+[«"]?([А-ЯA-Za-z][^\s,\.]{2,40})',
            text,
        )
        if legal_match:
            return legal_match.group(1).strip()

        return None
