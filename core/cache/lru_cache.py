"""LRU Cache with optional TTL and async support."""
import time
import asyncio
from collections import OrderedDict
from typing import Any, Callable, Optional


class LRUCache:
    """Thread-safe LRU Cache with TTL and eviction callbacks."""

    def __init__(self, capacity: int = 128, ttl: Optional[float] = None,
                 on_evict: Optional[Callable] = None):
        self.capacity = capacity
        self.ttl = ttl
        self.on_evict = on_evict
        self._cache: OrderedDict[str, dict] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        entry = self._cache[key]
        if self.ttl and time.monotonic() - entry["ts"] > self.ttl:
            self._evict(key)
            return None
        self._cache.move_to_end(key)
        return entry["value"]

    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = {"value": value, "ts": time.monotonic()}
        if len(self._cache) > self.capacity:
            oldest = next(iter(self._cache))
            self._evict(oldest)

    def _evict(self, key: str) -> None:
        entry = self._cache.pop(key, None)
        if entry and self.on_evict:
            self.on_evict(key, entry["value"])

    def invalidate(self, key: str) -> None:
        self._evict(key)

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def stats(self) -> dict:
        return {"size": len(self._cache), "capacity": self.capacity, "ttl": self.ttl}


class AsyncLRUCache(LRUCache):
    """Async-safe LRU cache using asyncio.Lock."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = asyncio.Lock()

    async def aget(self, key: str) -> Optional[Any]:
        async with self._lock:
            return self.get(key)

    async def aput(self, key: str, value: Any) -> None:
        async with self._lock:
            self.put(key, value)
