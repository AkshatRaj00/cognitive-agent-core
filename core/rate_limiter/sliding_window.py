"""Sliding window rate limiter."""
import time
from collections import deque
from threading import Lock


class SlidingWindowLimiter:
    """Sliding window counter for rate limiting."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self._timestamps: deque = deque()
        self._lock = Lock()

    def allow(self) -> bool:
        now = time.monotonic()
        with self._lock:
            cutoff = now - self.window
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                return True
            return False

    def remaining(self) -> int:
        now = time.monotonic()
        with self._lock:
            cutoff = now - self.window
            active = sum(1 for t in self._timestamps if t >= cutoff)
            return max(0, self.max_requests - active)
