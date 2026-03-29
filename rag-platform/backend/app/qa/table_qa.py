"""
Table QA Engine
Programmatically extracts numeric answers from financial table chunks.
Avoids LLM for direct numeric lookups — faster and more reliable.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

from app.models.schemas import DocumentChunk, TableChunk
from app.qa.classifier import QueryAnalysis

logger = structlog.get_logger(__name__)


class TableQAEngine:
    """
    Extracts numeric answers directly from TableChunk data.

    Approach:
    1. Find the column most likely to contain the target metric
    2. Find the row most likely to match the target year or category
    3. Return the cell value with source attribution
    4. Fall back to None if no confident match found
    """

    # Minimum confidence to return a programmatic answer
    MIN_CONFIDENCE = 0.6

    def extract_answer(
        self,
        chunks: List[Union[DocumentChunk, TableChunk]],
        analysis: QueryAnalysis,
        question: str,
    ) -> Optional[Tuple[str, float, List[TableChunk]]]:
        """
        Try to extract a numeric answer from retrieved table chunks.

        Args:
            chunks: Retrieved chunks (mix of text and table).
            analysis: Query analysis with extracted entities.
            question: Original question for display.

        Returns:
            (answer_text, confidence, matching_table_chunks) or None if no match.
        """
        table_chunks = [c for c in chunks if isinstance(c, TableChunk)]
        if not table_chunks:
            return None

        best_answer = None
        best_confidence = 0.0
        best_tables: List[TableChunk] = []

        for table_chunk in table_chunks:
            result = self._search_table(table_chunk, analysis)
            if result and result[1] > best_confidence:
                best_answer, best_confidence, matching_rows = result
                best_tables = [table_chunk]

        if best_answer and best_confidence >= self.MIN_CONFIDENCE:
            logger.info(
                "Table QA found answer",
                confidence=best_confidence,
                answer=str(best_answer)[:100],
            )
            return self._format_answer(best_answer, analysis, best_tables), best_confidence, best_tables

        return None

    def _search_table(
        self,
        table_chunk: TableChunk,
        analysis: QueryAnalysis,
    ) -> Optional[Tuple[Any, float, List[Dict]]]:
        """Search a single table for the answer."""
        if not table_chunk.raw_data or not table_chunk.headers:
            return None

        # Find the most relevant column
        target_col, col_confidence = self._find_metric_column(
            table_chunk.headers, analysis.target_metric
        )
        if not target_col:
            return None

        # Find the most relevant row (by year or category)
        target_rows = self._find_target_rows(
            table_chunk.raw_data, analysis.target_year, table_chunk.headers
        )

        if not target_rows:
            # Use all rows if no year filter
            target_rows = table_chunk.raw_data[:5]

        # Extract cell value(s)
        values = []
        for row in target_rows:
            val = row.get(target_col)
            if val is not None:
                values.append(val)

        if not values:
            return None

        # Take most recent / most relevant value
        value = values[0]
        confidence = col_confidence * (0.9 if analysis.target_year else 0.7)
        return value, confidence, target_rows

    def _find_metric_column(
        self, headers: List[str], target_metric: Optional[str]
    ) -> Tuple[Optional[str], float]:
        """
        Find the column header that best matches the target metric.
        Returns (column_name, confidence).
        """
        if not target_metric:
            return None, 0.0

        metric_synonyms = {
            "revenue": ["выручка", "revenue", "доходы", "daromad", "tushum", "реализация"],
            "profit": ["прибыль", "profit", "фойда", "foyda", "доход", "чистая прибыль"],
            "assets": ["активы", "assets", "активлар", "aktivlar", "баланс"],
            "liabilities": ["обязательства", "liabilities", "majburiyat"],
            "equity": ["капитал", "equity", "kapital", "собственный"],
            "loss": ["убыток", "loss", "zarar"],
        }

        synonyms = metric_synonyms.get(target_metric, [target_metric])

        best_col = None
        best_score = 0.0

        for header in headers:
            h_lower = header.lower()
            for syn in synonyms:
                if syn.lower() in h_lower:
                    # Exact contains match
                    score = 0.9 if h_lower == syn.lower() else 0.75
                    if score > best_score:
                        best_score = score
                        best_col = header

        return best_col, best_score

    def _find_target_rows(
        self,
        rows: List[Dict[str, Any]],
        target_year: Optional[int],
        headers: List[str],
    ) -> List[Dict[str, Any]]:
        """Find rows matching the target year."""
        if not target_year:
            return []

        matching = []
        year_str = str(target_year)

        # Find year column
        year_col = None
        for h in headers:
            if any(kw in h.lower() for kw in ["год", "year", "yil", "период", "дата", "sana", "davr"]):
                year_col = h
                break

        for row in rows:
            # Check year column
            if year_col and row.get(year_col) is not None:
                if year_str in str(row.get(year_col, "")):
                    matching.append(row)
                    continue

            # Check all cell values for the year
            row_text = " ".join(str(v) for v in row.values() if v is not None)
            if year_str in row_text:
                matching.append(row)

        return matching

    def _format_answer(
        self,
        value: Any,
        analysis: QueryAnalysis,
        tables: List[TableChunk],
    ) -> str:
        """
        Format the extracted value into a complete, natural Uzbek sentence.
        Returns a well-structured answer suitable for display to end users.
        """
        metric_names_uz = {
            "revenue": "daromad (tushum)",
            "profit": "sof foyda",
            "assets": "jami aktivlar",
            "liabilities": "majburiyatlar",
            "equity": "o'z kapitali (kapital)",
            "loss": "sof zarar",
            "employees": "xodimlar soni",
        }

        metric_label = metric_names_uz.get(
            analysis.target_metric or "", "moliyaviy ko'rsatkich"
        )

        # Format the numeric value with thousands separators
        if isinstance(value, float):
            if value == int(value):
                formatted_value = f"{value:,.0f}"
            else:
                formatted_value = f"{value:,.2f}"
        elif isinstance(value, int):
            formatted_value = f"{value:,}"
        else:
            formatted_value = str(value).strip()

        # Build the source reference
        source_file = tables[0].metadata.file_name if tables else "noma'lum hujjat"
        company = tables[0].metadata.company if tables else ""
        sheet = tables[0].sheet_name if tables and tables[0].sheet_name else None

        # Build a natural Uzbek sentence
        year_str = f"{analysis.target_year} yil uchun " if analysis.target_year else ""
        company_str = f"{company} kompaniyasining " if company else ""
        sheet_str = f" ('{sheet}' varag'idan)" if sheet else ""

        answer = (
            f"{company_str}{year_str}{metric_label} {formatted_value} tashkil etadi"
            f"{sheet_str}.\n\n"
            f"📄 Manba: «{source_file}»"
        )

        return answer
