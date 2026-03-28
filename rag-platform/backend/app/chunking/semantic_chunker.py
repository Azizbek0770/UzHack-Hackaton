from __future__ import annotations

import re
from typing import Iterable, List

from app.core.text_normalization import TextNormalizer
from app.models.schemas import DocumentChunk


class SemanticChunker:
    """Chunk documents by semantic boundaries rather than fixed tokens."""

    def __init__(self, min_length: int = 200, max_length: int = 1200) -> None:
        self._min_length = min_length
        self._max_length = max_length
        self._normalizer = TextNormalizer()

    def chunk(self, documents: Iterable[DocumentChunk]) -> List[DocumentChunk]:
        """Split each document chunk into smaller semantic chunks."""

        output: List[DocumentChunk] = []
        for doc in documents:
            normalized_content = self._normalizer.normalize(doc.content)
            sections = self._split_sections(normalized_content)
            for section in sections:
                if len(section.strip()) < 5:
                    continue
                for subchunk in self._balance(self._split_by_script_transition(section)):
                    output.append(
                        DocumentChunk(
                            content=subchunk,
                            page_index=doc.page_index,
                            metadata=doc.metadata,
                        )
                    )
        return output

    def _split_sections(self, text: str) -> List[str]:
        """Split text into sections using headings and empty lines."""

        heading_pattern = re.compile(r"\n(?=[A-ZА-Я0-9][A-ZА-Я0-9\s\-]{3,}\n)")
        sections = heading_pattern.split(text.strip())
        if len(sections) == 1:
            sections = re.split(r"\n{2,}", text.strip())
        return [section.strip() for section in sections if section.strip()]

    def _balance(self, sections: List[str]) -> List[str]:
        """Balance chunk lengths to stay within target limits."""

        chunks: List[str] = []
        for text in sections:
            if len(text) <= self._max_length:
                chunks.append(text.strip())
                continue
            if self._is_table_like(text):
                chunks.extend(self._split_table_block(text))
                continue
            sentences = re.split(r"(?<=[.!?])\s+", text)
            buffer: List[str] = []
            current_length = 0
            for sentence in sentences:
                if not sentence.strip():
                    continue
                buffer.append(sentence)
                current_length += len(sentence)
                if current_length >= self._min_length:
                    chunks.append(" ".join(buffer).strip())
                    buffer = []
                    current_length = 0
            if buffer:
                chunks.append(" ".join(buffer).strip())
        return chunks

    @staticmethod
    def _is_table_like(text: str) -> bool:
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) < 3:
            return False
        numeric_heavy = sum(1 for line in lines if sum(char.isdigit() for char in line) >= 4)
        return numeric_heavy >= max(2, len(lines) // 3)

    def _split_table_block(self, text: str) -> List[str]:
        lines = [line for line in text.splitlines() if line.strip()]
        chunks: List[str] = []
        buffer: List[str] = []
        current = 0
        for line in lines:
            buffer.append(line)
            current += len(line)
            if current >= self._max_length:
                chunks.append("\n".join(buffer).strip())
                buffer = []
                current = 0
        if buffer:
            chunks.append("\n".join(buffer).strip())
        return chunks

    @staticmethod
    def _split_by_script_transition(text: str) -> List[str]:
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            return []
        sections: List[List[str]] = [[lines[0]]]
        previous_bucket = SemanticChunker._script_bucket(lines[0])
        for line in lines[1:]:
            current_bucket = SemanticChunker._script_bucket(line)
            if current_bucket != previous_bucket and len(sections[-1]) > 1:
                sections.append([line])
            else:
                sections[-1].append(line)
            previous_bucket = current_bucket
        return ["\n".join(section).strip() for section in sections if section]

    @staticmethod
    def _script_bucket(text: str) -> str:
        cyrillic = sum(1 for char in text if "А" <= char <= "я")
        latin = sum(1 for char in text if "a" <= char.lower() <= "z")
        if cyrillic > latin:
            return "cyrillic"
        if latin > cyrillic:
            return "latin"
        return "neutral"
