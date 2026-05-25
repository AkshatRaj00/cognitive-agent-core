"""rate_limiter.py — Token-bucket and sliding-window rate limiters for agent API calls."""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitExceeded(Exception):
    """Raised when a rate limit is violated in strict mode."""
    limiter_name: str
    wait_seconds: float

    def __str__(self) -> str:
        return (
            f"Rate limit '{self.limiter_name}' exceeded. "
            f"Retry after {self.wait_seconds:.2f}s."
        )


class TokenBucketLimiter:
    """Classic token-bucket rate limiter.

    Args:
        capacity:       Maximum tokens (burst limit).
        refill_rate:    Tokens added per second.
        name:           Human-readable label for error messages.
        strict:         If True, raises RateLimitExceeded instead of returning False.

    Example::

        limiter = TokenBucketLimiter(capacity=10, refill_rate=2.0, name="gemini-api")

        if limiter.acquire():
            call_gemini()
        else:
            print("Rate limited, try later")
    """

    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        *,
        name: str = "default",
        strict: bool = False,
    ) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.name = name
        self.strict = strict
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> bool:
        """Attempt to consume *tokens* from the bucket."""
        with self._lock:
            self._refill()
            wait = (tokens - self._tokens) / self.refill_rate if self._tokens < tokens else 0.0
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            if self.strict:
                raise RateLimitExceeded(limiter_name=self.name, wait_seconds=wait)
            return False

    def wait_and_acquire(self, tokens: float = 1.0, timeout: float = 30.0) -> bool:
        """Block until tokens are available or *timeout* seconds elapse."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.acquire(tokens):
                return True
            time.sleep(min(0.05, tokens / self.refill_rate))
        return False

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    @property
    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens


class SlidingWindowLimiter:
    """Sliding-window rate limiter: at most *max_calls* in the last *window* seconds.

    Thread-safe via internal lock. Suitable for per-user or per-endpoint limits.
    """

    def __init__(self, max_calls: int, window: float, *, name: str = "default", strict: bool = False) -> None:
        self.max_calls = max_calls
        self.window = window
        self.name = name
        self.strict = strict
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """Return True and record the call, or False if limit exceeded."""
        now = time.monotonic()
        with self._lock:
            cutoff = now - self.window
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            if len(self._timestamps) < self.max_calls:
                self._timestamps.append(now)
                return True
            wait = (self._timestamps[0] + self.window) - now if self._timestamps else 0.0
            if self.strict:
                raise RateLimitExceeded(limiter_name=self.name, wait_seconds=wait)
            return False

    @property
    def remaining(self) -> int:
        """Calls remaining in the current window."""
        now = time.monotonic()
        cutoff = now - self.window
        with self._lock:
            active = sum(1 for t in self._timestamps if t >= cutoff)
            return max(0, self.max_calls - active)
