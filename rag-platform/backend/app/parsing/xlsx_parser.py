from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from app.core.logger import get_logger
from app.core.text_normalization import TextNormalizer
from app.models.schemas import Metadata, TableChunk


class XlsxParser:
    """Parse XLSX files and convert sheets into structured JSON."""

    def __init__(self) -> None:
        self._logger = get_logger("xlsx_parser")
        self._normalizer = TextNormalizer()

    def parse(self, file_path: Path, company: str) -> List[TableChunk]:
        """Parse a workbook into table chunks."""

        try:
            workbook = pd.ExcelFile(file_path)
        except Exception as exc:
            self._logger.error("Workbook loading failed file=%s error=%s", file_path.name, exc)
            raise
        chunks: List[TableChunk] = []
        with workbook:
            for index, sheet_name in enumerate(workbook.sheet_names, start=1):
                try:
                    df = workbook.parse(sheet_name)
                except Exception as exc:
                    self._logger.warning(
                        "Sheet parsing failed file=%s sheet=%s error=%s",
                        file_path.name,
                        sheet_name,
                        exc,
                    )
                    continue
                normalized_df = df.rename(columns=lambda column: str(column).strip())
                normalized_df = normalized_df.fillna("")
                table_json = {
                    "sheet_name": self._normalizer.normalize(str(sheet_name)),
                    "columns": [self._normalizer.normalize(str(column)) for column in normalized_df.columns],
                    "rows": self._rows_to_json(normalized_df),
                }
                metadata = Metadata(company=company, doc_type="xlsx", file_name=file_path.name)
                chunks.append(
                    TableChunk(content=table_json, sheet_index=index, metadata=metadata)
                )
        if not chunks:
            self._logger.warning("No valid sheets extracted for file=%s", file_path.name)
        return chunks

    @staticmethod
    def _rows_to_json(df: pd.DataFrame) -> list[dict[str, str]]:
        """Convert dataframe rows to normalized string values."""

        normalizer = TextNormalizer()
        rows: list[dict[str, str]] = []
        for _, row in df.iterrows():
            record: dict[str, str] = {}
            for column, value in row.items():
                column_name = normalizer.normalize(str(column))
                if isinstance(value, float) and value.is_integer():
                    record[column_name] = str(int(value))
                else:
                    record[column_name] = normalizer.normalize(str(value))
            rows.append(record)
        return rows
