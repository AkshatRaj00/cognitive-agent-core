"""memory_store.py — Persistent key-value memory with TTL-based expiry and pruning."""

import time
import threading
from typing import Any, Optional


class MemoryStore:
    """Thread-safe in-memory store with optional TTL expiry per entry.

    Entries older than their TTL are lazily removed on next access and
    also periodically pruned by a background thread started on init.
    """

    def __init__(self, default_ttl: Optional[float] = None, prune_interval: float = 60.0):
        """Initialise the store.

        Args:
            default_ttl: Default time-to-live in seconds for stored entries.
                         None means entries never expire by default.
            prune_interval: How often (seconds) the background pruner runs.
        """
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self._prune_interval = prune_interval
        self._stop_event = threading.Event()
        self._pruner = threading.Thread(target=self._prune_loop, daemon=True)
        self._pruner.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store *value* under *key* with an optional TTL override.

        Args:
            key:   Storage key.
            value: Arbitrary Python object to store.
            ttl:   Per-entry TTL in seconds.  Falls back to *default_ttl*.
                   Pass ``0`` or a negative value to store without expiry.
        """
        effective_ttl = ttl if ttl is not None else self.default_ttl
        expires_at = (time.monotonic() + effective_ttl) if effective_ttl and effective_ttl > 0 else None
        with self._lock:
            self._store[key] = {"value": value, "expires_at": expires_at}

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored under *key*, or *default* if absent/expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return default
            if self._is_expired(entry):
                del self._store[key]
                return default
            return entry["value"]

    def delete(self, key: str) -> bool:
        """Remove *key* from the store.  Returns True if the key existed."""
        with self._lock:
            return self._store.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        """Return True if *key* exists and has not expired."""
        return self.get(key, _SENTINEL) is not _SENTINEL

    def keys(self) -> list[str]:
        """Return a snapshot of all non-expired keys."""
        now = time.monotonic()
        with self._lock:
            return [
                k for k, v in self._store.items()
                if not self._is_expired(v, now=now)
            ]

    def clear(self) -> None:
        """Remove all entries from the store."""
        with self._lock:
            self._store.clear()

    def shutdown(self) -> None:
        """Stop the background pruner thread gracefully."""
        self._stop_event.set()
        self._pruner.join(timeout=2.0)

    def __len__(self) -> int:
        return len(self.keys())

    def __repr__(self) -> str:  # pragma: no cover
        return f"MemoryStore(entries={len(self)}, default_ttl={self.default_ttl})"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_expired(entry: dict[str, Any], *, now: Optional[float] = None) -> bool:
        expires_at = entry.get("expires_at")
        if expires_at is None:
            return False
        return (now if now is not None else time.monotonic()) >= expires_at

    def _prune_loop(self) -> None:
        """Background thread: periodically evict expired entries."""
        while not self._stop_event.wait(timeout=self._prune_interval):
            with self._lock:
                expired_keys = [
                    k for k, v in self._store.items() if self._is_expired(v)
                ]
                for k in expired_keys:
                    del self._store[k]


# Sentinel object used by exists() to distinguish None values from missing keys.
_SENTINEL = object()
