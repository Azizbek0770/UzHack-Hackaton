from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Sequence, Tuple, Union

from rank_bm25 import BM25Okapi

from app.models.schemas import DocumentChunk, Metadata, TableChunk

ChunkType = Union[DocumentChunk, TableChunk]


class BM25Store:
    """BM25 keyword index for hybrid retrieval."""

    def __init__(self) -> None:
        self._chunks: List[ChunkType] = []
        self._tokenized: List[List[str]] = []
        self._bm25: BM25Okapi | None = None

    def add(self, chunks: Sequence[ChunkType]) -> None:
        """Add chunks to the BM25 index."""

        if not chunks:
            return
        texts = [self._chunk_to_text(chunk) for chunk in chunks]
        tokenized = [text.lower().split() for text in texts]
        self._chunks.extend(chunks)
        self._tokenized.extend(tokenized)
        self._bm25 = BM25Okapi(self._tokenized)

    def save(self, storage_path: Path) -> None:
        """Persist BM25 tokenized corpus and chunks."""

        storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "tokenized": self._tokenized,
            "chunks": [self._serialize_chunk(chunk) for chunk in self._chunks],
        }
        storage_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def load(self, storage_path: Path) -> bool:
        """Load BM25 state from disk."""

        if not storage_path.exists():
            return False
        payload = json.loads(storage_path.read_text(encoding="utf-8"))
        self._tokenized = [list(tokens) for tokens in payload.get("tokenized", [])]
        self._chunks = [self._deserialize_chunk(item) for item in payload.get("chunks", [])]
        self._bm25 = BM25Okapi(self._tokenized) if self._tokenized else None
        return self._bm25 is not None

    def reset(self) -> None:
        """Reset in-memory BM25 state."""

        self._chunks = []
        self._tokenized = []
        self._bm25 = None

    def size(self) -> int:
        """Return number of chunks indexed in BM25."""

        return len(self._chunks)

    def search(self, query: str, top_k: int) -> List[Tuple[ChunkType, float]]:
        """Retrieve top-k chunks using BM25."""

        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(query.lower().split())
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        results: List[Tuple[ChunkType, float]] = []
        for index, score in ranked[:top_k]:
            results.append((self._chunks[index], float(score)))
        return results

    @staticmethod
    def _chunk_to_text(chunk: ChunkType) -> str:
        """Normalize chunk content to string."""

        if isinstance(chunk, DocumentChunk):
            return chunk.content
        return " ".join(
            [
                chunk.content.get("sheet_name", ""),
                " ".join(chunk.content.get("columns", [])),
                " ".join(str(row) for row in chunk.content.get("rows", [])[:5]),
            ]
        )

    @staticmethod
    def _serialize_chunk(chunk: ChunkType) -> dict[str, Any]:
        """Serialize chunk for persistence."""

        if isinstance(chunk, DocumentChunk):
            return {
                "kind": "document",
                "content": chunk.content,
                "page_index": chunk.page_index,
                "metadata": chunk.metadata.model_dump(),
            }
        return {
            "kind": "table",
            "content": chunk.content,
            "sheet_index": chunk.sheet_index,
            "metadata": chunk.metadata.model_dump(),
        }

    @staticmethod
    def _deserialize_chunk(data: dict[str, Any]) -> ChunkType:
        """Deserialize chunk from persisted payload."""

        metadata = Metadata(**data["metadata"])
        if data["kind"] == "document":
            return DocumentChunk(
                content=str(data["content"]),
                page_index=int(data["page_index"]),
                metadata=metadata,
            )
        return TableChunk(
            content=dict(data["content"]),
            sheet_index=int(data["sheet_index"]),
            metadata=metadata,
        )
