from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.config import RetrievalSettings
from app.models.schemas import DocumentChunk, Metadata
from app.retrieval.bm25_store import BM25Store
from app.retrieval.faiss_store import FaissStore
from app.retrieval.hybrid import HybridRetriever


class DummyEmbedder:
    """Deterministic embedder for testing persistence."""

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        return np.array([[float(len(text))] for text in texts], dtype="float32")


def test_hybrid_retriever_persistence_roundtrip(tmp_path: Path) -> None:
    """Hybrid retriever state can be persisted and loaded."""

    metadata = Metadata(company="Acme", doc_type="pdf", file_name="doc.pdf")
    chunks = [DocumentChunk(content="Revenue increased sharply", page_index=0, metadata=metadata)]
    embedder = DummyEmbedder()

    retriever = HybridRetriever(
        text_store=FaissStore(embedder),
        table_store=FaissStore(embedder),
        bm25_store=BM25Store(),
        settings=RetrievalSettings(text_top_k=2, table_top_k=2),
    )
    retriever.add_text_chunks(chunks)
    retriever.save(tmp_path)

    loaded = HybridRetriever(
        text_store=FaissStore(embedder),
        table_store=FaissStore(embedder),
        bm25_store=BM25Store(),
        settings=RetrievalSettings(text_top_k=2, table_top_k=2),
    )
    assert loaded.load(tmp_path)
    results = loaded.retrieve("Revenue")
    assert results
    assert results[0][0].metadata.company == "Acme"
