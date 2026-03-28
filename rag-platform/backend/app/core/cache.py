from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CacheItem:
    """Container for cached values with TTL tracking."""

    value: Any
    expires_at: float


class InMemoryCache:
    """Simple in-memory cache for query responses."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._data: Dict[str, CacheItem] = {}

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if still valid."""

        item = self._data.get(key)
        if not item:
            return None
        if item.expires_at < time.time():
            self._data.pop(key, None)
            return None
        return item.value

    def set(self, key: str, value: Any) -> None:
        """Store a value with TTL."""

        self._data[key] = CacheItem(value=value, expires_at=time.time() + self._ttl_seconds)

    def clear(self) -> None:
        """Clear all cached entries."""

        self._data.clear()
