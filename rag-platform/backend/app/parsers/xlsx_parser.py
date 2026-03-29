"""
XLSX Parser — pandas-based financial spreadsheet extraction.
Handles multi-sheet workbooks, preserves headers, normalizes numeric values,
and produces both TableChunk (structured) and DocumentChunk (text summary).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from app.core.config import settings
from app.models.schemas import (
    ChunkType,
    DocumentChunk,
    DocumentMetadata,
    Language,
    TableChunk,
)
from app.parsers.base import BaseParser
from app.utils.text import clean_text, is_meaningful

logger = structlog.get_logger(__name__)


class XLSXParser(BaseParser):
    """
    Parses XLSX/XLS financial spreadsheets into TableChunks and DocumentChunks.

    Strategy per sheet:
    1. Detect header row (first non-empty row)
    2. Normalize numeric strings (remove spaces, replace commas)
    3. Build row-dict list for structured storage
    4. Generate a text summary for embedding alongside raw data
    5. Also emit a DocumentChunk (text) so BM25 can index the content
    """

    # Financial metric keywords for column detection
    METRIC_PATTERNS = {
        "revenue": ["выручка", "revenue", "daromad", "доходы"],
        "assets": ["активы", "assets", "aktivlar"],
        "profit": ["прибыль", "profit", "foyda", "чистая прибыль"],
        "liabilities": ["обязательства", "liabilities", "majburiyatlar"],
        "equity": ["капитал", "equity", "kapital"],
        "year": ["год", "year", "yil", "период"],
    }

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".xlsx", ".xls", ".xlsm"}

    def parse(
        self, file_path: Path, metadata: DocumentMetadata
    ) -> List[DocumentChunk | TableChunk]:
        """
        Parse all sheets in an XLSX file.

        Returns both TableChunks (for structured QA) and
        DocumentChunks (text summaries, for semantic search).
        """
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("pandas not installed. Run: pip install pandas openpyxl")

        all_chunks: List[DocumentChunk | TableChunk] = []

        try:
            xl = pd.ExcelFile(str(file_path), engine="openpyxl")
            sheet_names = xl.sheet_names
            logger.info(
                "Parsing XLSX",
                file=file_path.name,
                sheets=len(sheet_names),
                company=metadata.company,
            )

            for sheet_idx, sheet_name in enumerate(sheet_names):
                try:
                    sheet_chunks = self._parse_sheet(
                        xl, sheet_name, sheet_idx, metadata
                    )
                    all_chunks.extend(sheet_chunks)
                except Exception as e:
                    logger.warning(
                        "Sheet parsing failed",
                        sheet=sheet_name,
                        error=str(e),
                    )
                    continue

        except Exception as e:
            logger.error("XLSX parsing failed", file=str(file_path), error=str(e))
            raise

        logger.info(
            "XLSX parsed successfully",
            file=file_path.name,
            chunks=len(all_chunks),
        )
        return all_chunks

    def _parse_sheet(
        self,
        xl,
        sheet_name: str,
        sheet_idx: int,
        metadata: DocumentMetadata,
    ) -> List[DocumentChunk | TableChunk]:
        """Parse a single sheet into chunks."""
        import pandas as pd

        chunks: List[DocumentChunk | TableChunk] = []

        # Read with header detection
        df_raw = pd.read_excel(xl, sheet_name=sheet_name, header=None)
        if df_raw.empty:
            return chunks

        header_row = self._detect_header_row(df_raw)
        df = pd.read_excel(
            xl, sheet_name=sheet_name, header=header_row, engine="openpyxl"
        )
        df = self._normalize_dataframe(df)

        if df.empty or len(df.columns) == 0:
            return chunks

        # Build raw row data
        headers = [str(c) for c in df.columns]
        rows = df.to_dict(orient="records")
        rows = [self._serialize_row(r) for r in rows]

        # Generate text summary for embedding
        summary = self._generate_summary(sheet_name, headers, rows, metadata)

        if not is_meaningful(summary, min_chars=settings.CHUNK_MIN_CHARS):
            return chunks

        sheet_meta = metadata.model_copy()

        # 1. TableChunk — for structured Table QA
        table_chunk = TableChunk(
            chunk_id=str(uuid.uuid4()),
            summary=summary,
            raw_data=rows,
            headers=headers,
            sheet_name=sheet_name,
            sheet_index=sheet_idx,
            metadata=sheet_meta,
        )
        chunks.append(table_chunk)

        # 2. DocumentChunk (text) — for BM25 + semantic retrieval
        doc_chunk = DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            content=clean_text(summary),
            chunk_type=ChunkType.TABLE,
            metadata=sheet_meta,
            page=None,
            section=sheet_name,
        )
        chunks.append(doc_chunk)

        return chunks

    def _detect_header_row(self, df) -> int:
        """
        Find the first row that looks like a header.
        Heuristic: row with most non-null string values in first 10 rows.
        """
        import pandas as pd
        best_row = 0
        best_score = -1

        for i in range(min(10, len(df))):
            row = df.iloc[i]
            score = sum(1 for v in row if isinstance(v, str) and len(str(v).strip()) > 1)
            if score > best_score:
                best_score = score
                best_row = i

        return best_row

    def _normalize_dataframe(self, df) -> "pd.DataFrame":
        """
        Clean and normalize a dataframe:
        - Drop fully empty rows/columns
        - Normalize numeric strings (e.g. "1 234,5" → 1234.5)
        - Strip string whitespace
        """
        import pandas as pd

        df = df.dropna(how="all").dropna(axis=1, how="all")
        df.columns = [
            str(c).strip().replace("\n", " ")
            for c in df.columns
        ]

        for col in df.columns:
            df[col] = df[col].apply(self._normalize_cell)

        return df.reset_index(drop=True)

    def _normalize_cell(self, value: Any) -> Any:
        """Normalize a single cell value."""
        if value is None:
            return None

        s = str(value).strip()

        if s in {"nan", "None", "-", "—", ""}:
            return None

        # Try to parse as number (handles "1 234 567" and "1,234.56")
        cleaned = s.replace(" ", "").replace("\xa0", "").replace(",", ".")
        try:
            if "." in cleaned:
                return float(cleaned)
            return int(cleaned)
        except ValueError:
            return s

    def _serialize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a pandas row dict to JSON-serializable form."""
        import math
        result = {}
        for k, v in row.items():
            if v is None:
                result[str(k)] = None
            elif isinstance(v, float) and math.isnan(v):
                result[str(k)] = None
            else:
                result[str(k)] = v
        return result

    def _generate_summary(
        self,
        sheet_name: str,
        headers: List[str],
        rows: List[Dict[str, Any]],
        metadata: DocumentMetadata,
    ) -> str:
        """
        Generate a text summary of the sheet for embedding.
        Includes company, sheet name, headers, and first few rows.
        """
        lines = [
            f"Компания: {metadata.company}",
            f"Лист: {sheet_name}",
            f"Файл: {metadata.file_name}",
            f"Столбцы: {', '.join(headers)}",
            "",
        ]

        # Include up to 20 rows as readable text
        for row in rows[:20]:
            parts = [f"{k}: {v}" for k, v in row.items() if v is not None]
            if parts:
                lines.append(" | ".join(parts))

        if len(rows) > 20:
            lines.append(f"... и ещё {len(rows) - 20} строк")

        return "\n".join(lines)
