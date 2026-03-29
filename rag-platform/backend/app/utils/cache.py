"""
Query Cache — Thread-safe LRU cache for query responses.
"""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional

import structlog

from app.models.schemas import CachedResponse, QueryResponse

logger = structlog.get_logger(__name__)


class QueryCache:
    """
    Thread-safe LRU cache with TTL expiration.
    Keyed by SHA-256 of the normalized question string.
    """

    def __init__(self, enabled: bool = True, max_size: int = 512, ttl_seconds: int = 3600):
        self.enabled = enabled
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self._store: OrderedDict[str, CachedResponse] = OrderedDict()
        self._lock = threading.Lock()

    def _key(self, question: str) -> str:
        """Normalize and hash the question for cache key."""
        normalized = question.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def get(self, question: str) -> Optional[CachedResponse]:
        if not self.enabled:
            return None

        key = self._key(question)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None

            # Check TTL
            if datetime.utcnow() - entry.cached_at > self.ttl:
                del self._store[key]
                return None

            # Move to end (LRU)
            self._store.move_to_end(key)
            entry.hit_count += 1
            return entry

    def set(self, question: str, response: QueryResponse) -> None:
        if not self.enabled:
            return

        key = self._key(question)
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = CachedResponse(response=response)

            # Evict oldest if over capacity
            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
        logger.info("Cache cleared")

    @property
    def size(self) -> int:
        return len(self._store)
