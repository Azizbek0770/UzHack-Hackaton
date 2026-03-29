"""
FAISS Vector Index
Maintains separate indexes for text chunks and table chunks.
Supports serialization/deserialization for persistence across restarts.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import structlog

from app.core.config import settings
from app.models.schemas import DocumentChunk, TableChunk

logger = structlog.get_logger(__name__)

# Type for retrieved results: (chunk, score)
RetrievalResult = List[Tuple[Union[DocumentChunk, TableChunk], float]]


class FAISSIndex:
    """
    Wrapper around a FAISS index for a single chunk type.

    Stores:
    - FAISS index for fast ANN search
    - List of chunks (mapping from vector ID → chunk)
    """

    def __init__(self, name: str, dim: int):
        self.name = name
        self.dim = dim
        self._index = None
        self._chunks: List[Union[DocumentChunk, TableChunk]] = []

    def build(self, chunks: List[Union[DocumentChunk, TableChunk]]) -> None:
        """
        Build the FAISS index from embedded chunks.
        Chunks must have .embedding populated.
        """
        try:
            import faiss
        except ImportError:
            raise RuntimeError("faiss-cpu not installed. Run: pip install faiss-cpu")

        valid_chunks = [c for c in chunks if c.embedding is not None]
        if not valid_chunks:
            logger.warning("No embedded chunks to index", index=self.name)
            return

        vectors = np.array([c.embedding for c in valid_chunks], dtype=np.float32)
        n, d = vectors.shape

        logger.info("Building FAISS index", name=self.name, vectors=n, dim=d)

        # IVFFlat for larger datasets, Flat for small/exact
        if n > 1000 and settings.FAISS_INDEX_TYPE == "IVFFlat":
            quantizer = faiss.IndexFlatIP(d)  # inner product (cosine, since L2 normalized)
            index = faiss.IndexIVFFlat(
                quantizer, d, min(settings.FAISS_NLIST, n // 5), faiss.METRIC_INNER_PRODUCT
            )
            index.train(vectors)
            index.nprobe = settings.FAISS_NPROBE
        else:
            # Flat index — exact, works for any size
            index = faiss.IndexFlatIP(d)

        index.add(vectors)
        self._index = index
        self._chunks = valid_chunks

        logger.info(
            "FAISS index built",
            name=self.name,
            total=index.ntotal,
        )

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        company_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> RetrievalResult:
        """
        Search the index for nearest neighbors.

        Args:
            query_vector: Shape (1, dim) float32 array.
            top_k: Number of results to retrieve.
            company_filter: If set, only return chunks from this company.
            doc_type_filter: If set, only return chunks of this doc type.

        Returns:
            List of (chunk, score) pairs, sorted by score descending.
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        # Over-fetch to account for filtering
        fetch_k = min(top_k * 5, self._index.ntotal)
        scores, indices = self._index.search(query_vector, fetch_k)

        results: RetrievalResult = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue

            chunk = self._chunks[idx]

            # Apply filters
            if company_filter and chunk.metadata.company.lower() != company_filter.lower():
                continue
            if doc_type_filter and chunk.metadata.doc_type.value != doc_type_filter:
                continue

            results.append((chunk, float(score)))
            if len(results) >= top_k:
                break

        return results

    def add_chunks(self, chunks: List[Union[DocumentChunk, TableChunk]]) -> None:
        """Add new chunks to an existing index (incremental update)."""
        try:
            import faiss
        except ImportError:
            raise RuntimeError("faiss-cpu not installed")

        valid = [c for c in chunks if c.embedding is not None]
        if not valid:
            return

        vectors = np.array([c.embedding for c in valid], dtype=np.float32)

        if self._index is None:
            self.build(valid)
        else:
            self._index.add(vectors)
            self._chunks.extend(valid)

    @property
    def size(self) -> int:
        return len(self._chunks)

    def save(self, path: Path) -> None:
        """Serialize index and chunk list to disk."""
        import faiss

        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(path / f"{self.name}.faiss"))

        with open(path / f"{self.name}_chunks.pkl", "wb") as f:
            # Exclude embeddings from pickle to save space
            chunks_no_emb = []
            for c in self._chunks:
                c_copy = c.model_copy()
                c_copy.embedding = None
                chunks_no_emb.append(c_copy)
            pickle.dump(chunks_no_emb, f)

        logger.info("Index saved", name=self.name, path=str(path))

    def load(self, path: Path) -> bool:
        """Load index from disk. Returns True on success."""
        import faiss

        index_path = path / f"{self.name}.faiss"
        chunks_path = path / f"{self.name}_chunks.pkl"

        if not index_path.exists() or not chunks_path.exists():
            return False

        try:
            self._index = faiss.read_index(str(index_path))
            with open(chunks_path, "rb") as f:
                self._chunks = pickle.load(f)

            logger.info(
                "Index loaded",
                name=self.name,
                total=self._index.ntotal,
            )
            return True
        except Exception as e:
            logger.error("Failed to load index", name=self.name, error=str(e))
            return False


class IndexManager:
    """
    Manages two separate FAISS indexes:
    - text_index: for DocumentChunks (prose text)
    - table_index: for TableChunks (financial tables)
    """

    def __init__(self, dim: int = settings.EMBEDDING_DIM):
        self.dim = dim
        self.text_index = FAISSIndex("text", dim)
        self.table_index = FAISSIndex("table", dim)

    def build_from_chunks(
        self,
        chunks: List[Union[DocumentChunk, TableChunk]],
    ) -> None:
        """Split chunks by type and build both indexes."""
        text_chunks = [c for c in chunks if isinstance(c, DocumentChunk)]
        table_chunks = [c for c in chunks if isinstance(c, TableChunk)]

        logger.info(
            "Building indexes",
            text_chunks=len(text_chunks),
            table_chunks=len(table_chunks),
        )

        if text_chunks:
            self.text_index.build(text_chunks)
        if table_chunks:
            self.table_index.build(table_chunks)

    def search_text(self, query_vec: np.ndarray, top_k: int, **filters) -> RetrievalResult:
        return self.text_index.search(query_vec, top_k, **filters)

    def search_table(self, query_vec: np.ndarray, top_k: int, **filters) -> RetrievalResult:
        return self.table_index.search(query_vec, top_k, **filters)

    def save(self, path: Path) -> None:
        self.text_index.save(path)
        self.table_index.save(path)

    def load(self, path: Path) -> bool:
        text_ok = self.text_index.load(path)
        table_ok = self.table_index.load(path)
        return text_ok or table_ok  # partial load is acceptable
