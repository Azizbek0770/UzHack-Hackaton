from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Sequence, Tuple, Union

import faiss
import numpy as np

from app.embeddings.embedder import EmbeddingModel
from app.models.schemas import DocumentChunk, Metadata, TableChunk

ChunkType = Union[DocumentChunk, TableChunk]


class FaissStore:
    """FAISS-based vector store for dense retrieval."""

    def __init__(self, embedder: EmbeddingModel) -> None:
        self._embedder = embedder
        self._index: faiss.IndexFlatIP | None = None
        self._chunks: List[ChunkType] = []

    def add(self, chunks: Sequence[ChunkType]) -> None:
        """Add chunks to the vector store."""

        if not chunks:
            return
        texts = [self._chunk_to_text(chunk) for chunk in chunks]
        embeddings = self._embedder.encode(texts)
        if self._index is None:
            self._index = faiss.IndexFlatIP(embeddings.shape[1])
        elif self._index.d != embeddings.shape[1]:
            self.reset()
            self._index = faiss.IndexFlatIP(embeddings.shape[1])
        self._index.add(embeddings)
        self._chunks.extend(chunks)

    def save(self, index_path: Path, chunks_path: Path) -> None:
        """Persist vector index and chunks to disk."""

        if self._index is None:
            return
        index_path.parent.mkdir(parents=True, exist_ok=True)
        chunks_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(index_path))
        serialized = [self._serialize_chunk(chunk) for chunk in self._chunks]
        chunks_path.write_text(json.dumps(serialized, ensure_ascii=False), encoding="utf-8")

    def load(self, index_path: Path, chunks_path: Path) -> bool:
        """Load vector index and chunks if persisted."""

        if not index_path.exists() or not chunks_path.exists():
            return False
        loaded_index = faiss.read_index(str(index_path))
        probe = self._embedder.encode(["dimension probe"])
        expected_dim = int(probe.shape[1]) if probe.ndim == 2 and probe.shape[0] > 0 else 0
        if expected_dim <= 0 or loaded_index.d != expected_dim:
            self.reset()
            return False
        self._index = loaded_index
        raw_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        self._chunks = [self._deserialize_chunk(item) for item in raw_chunks]
        return True

    def reset(self) -> None:
        """Clear indexed vectors and chunk references."""

        self._index = None
        self._chunks = []

    def size(self) -> int:
        """Return number of chunks currently indexed."""

        return len(self._chunks)

    def search(self, query: str, top_k: int) -> List[Tuple[ChunkType, float]]:
        """Search for top-k similar chunks."""

        if self._index is None or not self._chunks:
            return []
        query_vector = self._embedder.encode([query])
        scores, indices = self._index.search(query_vector, top_k)
        results: List[Tuple[ChunkType, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0:
                continue
            results.append((self._chunks[idx], float(score)))
        return results

    @staticmethod
    def _chunk_to_text(chunk: ChunkType) -> str:
        """Normalize chunk content to string for embeddings."""

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
