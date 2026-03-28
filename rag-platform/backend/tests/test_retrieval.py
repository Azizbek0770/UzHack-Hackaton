from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.models.schemas import DocumentChunk, Metadata
from app.retrieval.bm25_store import BM25Store
from app.retrieval.faiss_store import FaissStore
from app.retrieval.hybrid import HybridRetriever
from app.core.config import RetrievalSettings


class DummyEmbedder:
    """Deterministic embedder for testing."""

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        """Return deterministic embeddings."""

        return np.array([[float(len(text))] for text in texts], dtype="float32")


def test_hybrid_retriever_merges_scores() -> None:
    """Hybrid retriever returns ranked results."""

    embedder = DummyEmbedder()
    text_store = FaissStore(embedder)
    table_store = FaissStore(embedder)
    bm25_store = BM25Store()
    retriever = HybridRetriever(
        text_store=text_store,
        table_store=table_store,
        bm25_store=bm25_store,
        settings=RetrievalSettings(text_top_k=2, table_top_k=2),
    )
    metadata = Metadata(company="Acme", doc_type="pdf", file_name="doc.pdf")
    chunks = [
        DocumentChunk(content="Revenue increased", page_index=0, metadata=metadata),
        DocumentChunk(content="Profit stable", page_index=1, metadata=metadata),
    ]
    retriever.add_text_chunks(chunks)
    results = retriever.retrieve("Revenue", prefer_tables=False)
    assert results
    assert results[0][0].metadata.company == "Acme"
