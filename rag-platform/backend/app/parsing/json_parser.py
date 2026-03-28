from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.core.logger import get_logger
from app.core.text_normalization import TextNormalizer
from app.models.schemas import DocumentChunk, Metadata


class JsonParser:
    """Parse JSON metadata into document chunks."""

    def __init__(self) -> None:
        self._logger = get_logger("json_parser")
        self._normalizer = TextNormalizer()

    def parse(self, file_path: Path, company: str) -> List[DocumentChunk]:
        """Parse JSON file into a single chunk."""

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self._logger.warning("JSON parsing failed file=%s error=%s", file_path.name, exc)
            raise
        content = self._normalizer.normalize(json.dumps(data, ensure_ascii=False, indent=2))
        metadata = Metadata(company=company, doc_type="json", file_name=file_path.name)
        return [DocumentChunk(content=content, page_index=0, metadata=metadata)]
