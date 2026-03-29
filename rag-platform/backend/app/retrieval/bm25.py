"""
BM25 Keyword Retrieval Engine
Complements dense retrieval for exact-match and keyword-heavy queries.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Optional, Tuple, Union

import structlog

from app.models.schemas import DocumentChunk, TableChunk

logger = structlog.get_logger(__name__)

RetrievalResult = List[Tuple[Union[DocumentChunk, TableChunk], float]]


class BM25Retriever:
    """
    BM25 retriever over document chunks.

    Uses rank_bm25 for efficient BM25+ scoring.
    Tokenizes on whitespace + punctuation, lowercases.
    Handles Russian/Uzbek text without stemming (acceptable for BM25).
    """

    def __init__(self):
        self._bm25 = None
        self._chunks: List[Union[DocumentChunk, TableChunk]] = []
        self._tokenized_corpus: List[List[str]] = []

    def build(self, chunks: List[Union[DocumentChunk, TableChunk]]) -> None:
        """Build BM25 index from chunks."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise RuntimeError(
                "rank_bm25 not installed. Run: pip install rank-bm25"
            )

        self._chunks = chunks
        self._tokenized_corpus = [
            self._tokenize(self._get_text(c)) for c in chunks
        ]
        self._bm25 = BM25Okapi(self._tokenized_corpus)
        logger.info("BM25 index built", docs=len(chunks))

    def search(
        self,
        query: str,
        top_k: int = 10,
        company_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> RetrievalResult:
        """
        Search using BM25.

        Returns:
            List of (chunk, normalized_score) pairs.
        """
        if self._bm25 is None or not self._chunks:
            return []

        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        # Normalize scores to [0, 1]
        max_score = scores.max() if scores.max() > 0 else 1.0
        normalized = scores / max_score

        # Sort by score and apply filters
        indexed = sorted(enumerate(normalized), key=lambda x: x[1], reverse=True)
        results: RetrievalResult = []

        for idx, score in indexed:
            if score <= 0:
                break

            chunk = self._chunks[idx]

            if company_filter and chunk.metadata.company.lower() != company_filter.lower():
                continue
            if doc_type_filter and chunk.metadata.doc_type.value != doc_type_filter:
                continue

            results.append((chunk, float(score)))
            if len(results) >= top_k:
                break

        return results

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple whitespace + punctuation tokenizer.
        Lowercase, split on non-alphanumeric (handles Russian Cyrillic).
        """
        import re
        text = text.lower()
        tokens = re.split(r"[^\w\u0400-\u04FF\u0600-\u06FF]+", text)
        return [t for t in tokens if len(t) > 1]

    def _get_text(self, chunk: Union[DocumentChunk, TableChunk]) -> str:
        """Extract the embeddable text from a chunk."""
        if isinstance(chunk, TableChunk):
            return chunk.summary
        return chunk.content

    @property
    def size(self) -> int:
        return len(self._chunks)

    def save(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "bm25.pkl", "wb") as f:
            pickle.dump({
                "bm25": self._bm25,
                "chunks": self._chunks,
            }, f)
        logger.info("BM25 index saved", path=str(path))

    def load(self, path: Path) -> bool:
        pkl_path = path / "bm25.pkl"
        if not pkl_path.exists():
            return False
        try:
            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
            self._bm25 = data["bm25"]
            self._chunks = data["chunks"]
            logger.info("BM25 index loaded", docs=len(self._chunks))
            return True
        except Exception as e:
            logger.error("Failed to load BM25 index", error=str(e))
            return False
