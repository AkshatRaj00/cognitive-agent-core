"""
MemoryStore TTL Lazy Eviction Patch.

Fixes: expired keys returned on read before background sweeper runs.

The original get() did not check TTL on access. This patch adds
lazy eviction so expired keys return None immediately.
"""
from __future__ import annotations

import time
import threading
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTLEntry:
    """Container for a stored value with optional expiry timestamp."""
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: Optional[float]) -> None:
        self.value = value
        self.expires_at: Optional[float] = time.monotonic() + ttl if ttl else None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.monotonic() >= self.expires_at


class MemoryStoreTTLFixed:
    """
    Fixed MemoryStore with lazy TTL eviction.

    Key behaviour changes vs. original:
    - ``get()`` checks expiry on access and deletes + returns None immediately
    - Background sweeper still runs to free memory for keys that are never read
    - Thread-safe via ``threading.RLock``
    """

    def __init__(self, sweep_interval: float = 60.0) -> None:
        self._store: dict[str, TTLEntry] = {}
        self._lock = threading.RLock()
        self._sweep_interval = sweep_interval
        self._sweeper = threading.Thread(
            target=self._background_sweep,
            daemon=True,
            name="memory-store-sweeper",
        )
        self._sweeper.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store *value* under *key* with an optional TTL in seconds."""
        with self._lock:
            self._store[key] = TTLEntry(value, ttl)
            logger.debug("SET %r (ttl=%s)", key, ttl)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve the value for *key*.

        Returns *default* (``None``) if the key does not exist **or has expired**.
        Expired entries are deleted lazily on first access.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return default

            # ⭐ Lazy eviction — this is the bug fix
            if entry.is_expired:
                logger.debug("LAZY EVICT %r (expired)", key)
                del self._store[key]
                return default

            return entry.value

    def delete(self, key: str) -> bool:
        """Remove *key* from the store. Returns True if the key existed."""
        with self._lock:
            existed = key in self._store
            self._store.pop(key, None)
            return existed

    def exists(self, key: str) -> bool:
        """Return True only if *key* exists and has not expired."""
        return self.get(key) is not None

    def ttl_remaining(self, key: str) -> Optional[float]:
        """Return seconds remaining before *key* expires, or None if no TTL."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired:
                return 0.0
            if entry.expires_at is None:
                return None
            return max(0.0, entry.expires_at - time.monotonic())

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return sum(1 for e in self._store.values() if not e.is_expired)

    # ------------------------------------------------------------------
    # Background sweeper
    # ------------------------------------------------------------------

    def _background_sweep(self) -> None:
        """Periodically remove expired entries to reclaim memory."""
        import time as _time
        while True:
            _time.sleep(self._sweep_interval)
            with self._lock:
                expired_keys = [
                    k for k, e in self._store.items() if e.is_expired
                ]
                for k in expired_keys:
                    del self._store[k]
                if expired_keys:
                    logger.debug("Sweep removed %d expired keys", len(expired_keys))
