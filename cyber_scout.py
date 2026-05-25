"""cyber_scout.py — Async-ready recon pipeline with result caching."""

import hashlib
import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

_CACHE_DEFAULT_TTL = 300.0   # 5 minutes


class ReconCache:
    """Simple TTL cache for recon results keyed by query hash."""

    def __init__(self, ttl: float = _CACHE_DEFAULT_TTL) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self.ttl = ttl

    def _key(self, query: str) -> str:
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def get(self, query: str) -> Optional[Any]:
        key = self._key(query)
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, query: str, value: Any) -> None:
        key = self._key(query)
        self._store[key] = (value, time.monotonic() + self.ttl)

    def invalidate(self, query: str) -> None:
        self._store.pop(self._key(query), None)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        now = time.monotonic()
        return sum(1 for _, (_, exp) in self._store.items() if now < exp)


class CyberScout:
    """Recon pipeline that chains query handlers and caches results.

    Handlers are callables that accept a query string and return a dict
    of findings.  They are called in registration order and their
    results are merged.  Cached results bypass all handlers.
    """

    def __init__(self, cache_ttl: float = _CACHE_DEFAULT_TTL) -> None:
        self._handlers: list[tuple[str, Callable[[str], dict]]] = []
        self.cache = ReconCache(ttl=cache_ttl)

    def register_handler(self, name: str, handler: Callable[[str], dict]) -> None:
        """Add a recon handler to the pipeline."""
        self._handlers.append((name, handler))
        logger.debug("Registered recon handler: %s", name)

    def run(self, query: str, *, force_refresh: bool = False) -> dict[str, Any]:
        """Execute the full recon pipeline for *query*.

        Args:
            query:         The recon target / search query.
            force_refresh: Bypass cache and re-run all handlers.

        Returns:
            Merged dict of findings from all handlers.
        """
        if not force_refresh:
            cached = self.cache.get(query)
            if cached is not None:
                logger.debug("Cache hit for query: %.40s", query)
                return cached

        findings: dict[str, Any] = {}
        for name, handler in self._handlers:
            try:
                result = handler(query)
                if isinstance(result, dict):
                    findings.update(result)
                else:
                    findings[name] = result
                logger.debug("Handler '%s' returned %d finding(s)", name, len(findings))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Handler '%s' failed for query '%s': %s", name, query, exc)
                findings[f"{name}_error"] = str(exc)

        self.cache.set(query, findings)
        return findings
