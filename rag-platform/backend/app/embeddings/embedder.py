from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.logger import get_logger


class EmbeddingModel:
    """Multilingual embedding model wrapper."""

    def __init__(self, model_name: str) -> None:
        self._logger = get_logger("embedder")
        self._model = None
        self._fallback = False
        try:
            self._model = SentenceTransformer(model_name)
        except Exception as exc:
            self._fallback = True
            self._logger.warning("Falling back to lightweight embedder: %s", exc)

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        items = list(texts)
        if not items:
            return np.zeros((0, 2), dtype="float32")
        if self._fallback:
            return np.asarray([self._lightweight_vector(text) for text in items], dtype="float32")
        embeddings = self._model.encode(items, normalize_embeddings=True)
        return np.asarray(embeddings, dtype="float32")

    @staticmethod
    def _lightweight_vector(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        head = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
        numeric = (sum(char.isdigit() for char in text) + 1) / (len(text) + 1)
        return [float(len(text)), float(head + numeric)]
