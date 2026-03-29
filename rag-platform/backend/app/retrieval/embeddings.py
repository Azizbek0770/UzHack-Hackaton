"""
Embedding Engine — BAAI/bge-m3 Multilingual Embeddings
Handles batched encoding for both text and table chunks.
Memory-safe: processes in small sub-batches with explicit GC.
"""

from __future__ import annotations

import gc
import pickle
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import structlog

from app.core.config import settings
from app.core.logging import TimingLogger
from app.models.schemas import DocumentChunk, TableChunk

logger = structlog.get_logger(__name__)

# Maximum characters per text to keep tensors small
_MAX_TEXT_CHARS = 512


class EmbeddingEngine:
    """
    Wraps a sentence-transformers model (bge-m3) for multilingual embedding.

    BGE-M3 supports:
    - Russian, Uzbek, English (and 100+ languages)
    - Dense, sparse, and ColBERT retrieval (we use dense)
    - 1024-dim output vectors
    """

    def __init__(self):
        self._model = None
        self._model_name = settings.EMBEDDING_MODEL
        self._device = settings.EMBEDDING_DEVICE
        self._batch_size = settings.EMBEDDING_BATCH_SIZE

    def _load_model(self):
        """Lazy-load the embedding model."""
        if self._model is not None:
            return

        logger.info("Loading embedding model", model=self._model_name)
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self._model_name,
                device=self._device,
            )
            logger.info(
                "Embedding model loaded",
                model=self._model_name,
                device=self._device,
                dim=self._model.get_sentence_embedding_dimension(),
            )
        except ImportError:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of texts in memory-safe sub-batches.

        Args:
            texts: List of strings to embed.

        Returns:
            Float32 numpy array of shape (len(texts), embedding_dim).
        """
        self._load_model()

        # Truncate texts to avoid huge tensors
        texts = [t[:_MAX_TEXT_CHARS] for t in texts]

        all_embeddings: List[np.ndarray] = []
        sub_batch = self._batch_size  # small, memory-safe size

        logger.info("Embedding texts", total=len(texts), sub_batch=sub_batch)

        with TimingLogger("embed", logger, n=len(texts)):
            for start in range(0, len(texts), sub_batch):
                batch = texts[start: start + sub_batch]
                vecs = self._model.encode(
                    batch,
                    batch_size=sub_batch,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                )
                all_embeddings.append(vecs.astype(np.float32))

                # Free intermediate tensors after every sub-batch
                gc.collect()

                done = min(start + sub_batch, len(texts))
                if done % 100 == 0 or done == len(texts):
                    logger.debug("Embedding progress", done=done, total=len(texts))

        return np.vstack(all_embeddings)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query string.
        BGE-M3 recommends prefixing queries with "Represent this sentence: "
        for retrieval tasks.
        """
        self._load_model()
        # BGE instruction prefix improves retrieval quality
        prefixed = f"Represent this sentence for retrieval: {query}"
        vec = self._model.encode(
            prefixed,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vec.astype(np.float32).reshape(1, -1)

    def embed_chunks(
        self, chunks: List[Union[DocumentChunk, TableChunk]]
    ) -> List[Union[DocumentChunk, TableChunk]]:
        """
        Embed all chunks in-place, setting the .embedding field.

        Args:
            chunks: List of DocumentChunk or TableChunk.

        Returns:
            Same chunks with .embedding populated.
        """
        if not chunks:
            return chunks

        # Extract text to embed
        texts = []
        for chunk in chunks:
            if isinstance(chunk, TableChunk):
                texts.append(chunk.summary)
            else:
                texts.append(chunk.content)

        embeddings = self.embed_texts(texts)

        for chunk, vec in zip(chunks, embeddings):
            chunk.embedding = vec.tolist()

        logger.info("Chunks embedded", count=len(chunks))
        return chunks

    def get_dimension(self) -> int:
        """Return the embedding dimension."""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()
