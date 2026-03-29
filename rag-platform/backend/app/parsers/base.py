"""
Base Parser Abstract Class + JSON Parser
All parsers implement the BaseParser interface.
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union

import structlog

from app.models.schemas import (
    ChunkType,
    DocumentChunk,
    DocumentMetadata,
    TableChunk,
)
from app.utils.text import clean_text

logger = structlog.get_logger(__name__)

# Type alias for parser return values
ParseResult = List[Union[DocumentChunk, TableChunk]]


class BaseParser(ABC):
    """Abstract base class for all document parsers."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Return True if this parser handles the given file."""
        ...

    @abstractmethod
    def parse(self, file_path: Path, metadata: DocumentMetadata) -> ParseResult:
        """
        Parse a file and return a list of chunks.

        Args:
            file_path: Path to the document.
            metadata: Pre-populated document metadata from the ingestion layer.

        Returns:
            List of DocumentChunk or TableChunk objects.
        """
        ...


class JSONParser(BaseParser):
    """
    Parses JSON company metadata files.
    Converts flat/nested JSON into a single DocumentChunk.
    """

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".json"

    def parse(self, file_path: Path, metadata: DocumentMetadata) -> ParseResult:
        """Parse a JSON metadata file into a DocumentChunk."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("JSON parse error", file=str(file_path), error=str(e))
            return []
        except Exception as e:
            logger.error("Cannot read file", file=str(file_path), error=str(e))
            return []

        # Flatten nested JSON to human-readable text
        text = self._json_to_text(data, prefix="")

        if not text.strip():
            return []

        chunk = DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            content=clean_text(text),
            chunk_type=ChunkType.TEXT,
            metadata=metadata,
            page=None,
            section="company_metadata",
        )
        return [chunk]

    def _json_to_text(self, data, prefix: str, depth: int = 0) -> str:
        """Recursively convert JSON to readable key: value text."""
        lines = []
        indent = "  " * depth

        if isinstance(data, dict):
            for k, v in data.items():
                key = f"{prefix}{k}" if prefix else k
                if isinstance(v, (dict, list)):
                    lines.append(f"{indent}{k}:")
                    lines.append(self._json_to_text(v, prefix="", depth=depth + 1))
                else:
                    lines.append(f"{indent}{k}: {v}")

        elif isinstance(data, list):
            for i, item in enumerate(data[:50]):  # cap list length
                if isinstance(item, (dict, list)):
                    lines.append(self._json_to_text(item, prefix="", depth=depth))
                else:
                    lines.append(f"{indent}- {item}")
        else:
            lines.append(f"{indent}{data}")

        return "\n".join(lines)
