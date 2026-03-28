from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional, Tuple, Union

from app.core.config import RetrievalSettings
from app.models.schemas import DocumentChunk, TableChunk
from app.retrieval.bm25_store import BM25Store
from app.retrieval.faiss_store import FaissStore

ChunkType = Union[DocumentChunk, TableChunk]


class HybridRetriever:
    """Combine dense and keyword retrieval with weighted scoring."""

    def __init__(
        self,
        text_store: FaissStore,
        table_store: FaissStore,
        bm25_store: BM25Store,
        settings: RetrievalSettings,
    ) -> None:
        self._text_store = text_store
        self._table_store = table_store
        self._bm25_store = bm25_store
        self._settings = settings

    def add_text_chunks(self, chunks: Iterable[DocumentChunk]) -> None:
        """Index text chunks for retrieval."""

        chunk_list = list(chunks)
        self._text_store.add(chunk_list)
        self._bm25_store.add(chunk_list)

    def add_table_chunks(self, chunks: Iterable[TableChunk]) -> None:
        """Index table chunks for retrieval."""

        chunk_list = list(chunks)
        self._table_store.add(chunk_list)
        self._bm25_store.add(chunk_list)

    def reset(self) -> None:
        """Clear all retrieval stores."""

        self._text_store.reset()
        self._table_store.reset()
        self._bm25_store.reset()

    def stats(self) -> dict[str, int]:
        """Return index sizes for diagnostics."""

        return {
            "text_chunks": self._text_store.size(),
            "table_chunks": self._table_store.size(),
            "bm25_chunks": self._bm25_store.size(),
        }

    def save(self, storage_dir: Path) -> None:
        """Persist retrieval stores to disk."""

        storage_dir.mkdir(parents=True, exist_ok=True)
        self._text_store.save(
            storage_dir / "text.faiss",
            storage_dir / "text_chunks.json",
        )
        self._table_store.save(
            storage_dir / "table.faiss",
            storage_dir / "table_chunks.json",
        )
        self._bm25_store.save(storage_dir / "bm25.json")

    def load(self, storage_dir: Path) -> bool:
        """Load retrieval stores from disk if available."""

        text_loaded = self._text_store.load(
            storage_dir / "text.faiss",
            storage_dir / "text_chunks.json",
        )
        self._table_store.load(
            storage_dir / "table.faiss",
            storage_dir / "table_chunks.json",
        )
        bm25_loaded = self._bm25_store.load(storage_dir / "bm25.json")
        return text_loaded and bm25_loaded

    def retrieve(
        self,
        query: str,
        prefer_tables: bool = False,
        mode: Literal["table", "text", "hybrid"] | None = None,
        company: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> List[Tuple[ChunkType, float]]:
        """Retrieve and score top chunks for a query."""

        effective_mode = mode or ("table" if prefer_tables else "text")
        dense_top_k = self._settings.table_top_k if effective_mode == "table" else self._settings.text_top_k
        dense_results = self._dense_results_for_mode(query, effective_mode, dense_top_k)
        bm25_results = self._bm25_store.search(query, dense_top_k * 2)
        merged = self._merge_scores(dense_results, bm25_results)
        filtered = self._filter(merged, company=company, doc_type=doc_type)
        return filtered[: dense_top_k * 2]

    def _dense_results_for_mode(
        self,
        query: str,
        mode: Literal["table", "text", "hybrid"],
        top_k: int,
    ) -> List[Tuple[ChunkType, float]]:
        """Select dense retrieval strategy for query mode."""

        if mode == "table":
            return self._table_store.search(query, top_k)
        if mode == "text":
            return self._text_store.search(query, top_k)
        text_results = self._text_store.search(query, top_k)
        table_results = self._table_store.search(query, top_k)
        return text_results + table_results

    def _merge_scores(
        self,
        dense_results: List[Tuple[ChunkType, float]],
        bm25_results: List[Tuple[ChunkType, float]],
    ) -> List[Tuple[ChunkType, float]]:
        """Merge dense and BM25 scores into a unified ranking."""

        scores: Dict[str, float] = defaultdict(float)
        chunk_map: Dict[str, ChunkType] = {}
        if dense_results:
            max_dense = max(score for _, score in dense_results) or 1.0
            for chunk, score in dense_results:
                key = self._chunk_key(chunk)
                chunk_map[key] = chunk
                scores[key] += (score / max_dense) * self._settings.dense_weight
        if bm25_results:
            max_bm25 = max(score for _, score in bm25_results) or 1.0
            for chunk, score in bm25_results:
                key = self._chunk_key(chunk)
                chunk_map[key] = chunk
                scores[key] += (score / max_bm25) * self._settings.bm25_weight
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [
            (chunk_map[key], score)
            for key, score in ranked
            if score >= self._settings.min_merged_score
        ]

    @staticmethod
    def _chunk_key(chunk: ChunkType) -> str:
        """Build deterministic key to deduplicate same source spans."""

        location = chunk.page_index if isinstance(chunk, DocumentChunk) else chunk.sheet_index
        return f"{chunk.metadata.file_name}:{location}:{chunk.metadata.doc_type}:{chunk.metadata.company}"

    @staticmethod
    def _filter(
        results: List[Tuple[ChunkType, float]],
        company: Optional[str],
        doc_type: Optional[str],
    ) -> List[Tuple[ChunkType, float]]:
        """Filter results by metadata."""

        filtered: List[Tuple[ChunkType, float]] = []
        for chunk, score in results:
            if company and chunk.metadata.company != company:
                continue
            if doc_type and chunk.metadata.doc_type != doc_type:
                continue
            filtered.append((chunk, score))
        return filtered
