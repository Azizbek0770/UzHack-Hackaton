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
    def encode(self, texts: Iterable[str]) -> np.ndarray:
        vectors: list[list[float]] = []
        for text in texts:
            vectors.append([float(len(text)), float(sum(char.isdigit() for char in text) + 1)])
        return np.array(vectors, dtype="float32")


def test_retrieval_hit_rate_at_3() -> None:
    """Hybrid retrieval maintains acceptable hit-rate on multilingual finance fixtures."""

    documents = [
        DocumentChunk(
            content="Revenue for 2024 reached 1500 million sums.",
            page_index=0,
            metadata=Metadata(company="Acme", doc_type="pdf", file_name="en_report.pdf"),
        ),
        DocumentChunk(
            content="Выручка за 2024 год составила 1500 млн сум.",
            page_index=1,
            metadata=Metadata(company="Acme", doc_type="pdf", file_name="ru_report.pdf"),
        ),
        DocumentChunk(
            content="Daromad 2024 yilda 1500 mln so'mga yetdi.",
            page_index=2,
            metadata=Metadata(company="Acme", doc_type="pdf", file_name="uz_report.pdf"),
        ),
    ]
    retriever = HybridRetriever(
        text_store=FaissStore(DummyEmbedder()),
        table_store=FaissStore(DummyEmbedder()),
        bm25_store=BM25Store(),
        settings=RetrievalSettings(text_top_k=3, table_top_k=3),
    )
    retriever.add_text_chunks(documents)

    fixtures = [
        ("What is revenue in 2024?", "en_report.pdf"),
        ("Какая выручка за 2024?", "ru_report.pdf"),
        ("2024 daromad qancha?", "uz_report.pdf"),
    ]
    hits = 0
    for query, expected_file in fixtures:
        top_results = retriever.retrieve(query, mode="text")[:3]
        files = [chunk.metadata.file_name for chunk, _ in top_results]
        if expected_file in files:
            hits += 1
    hit_rate = hits / len(fixtures)
    assert hit_rate >= 0.66
