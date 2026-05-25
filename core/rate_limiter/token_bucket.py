"""Token Bucket rate limiter for API call throttling."""
import time
from threading import Lock


class TokenBucket:
    """Thread-safe token bucket algorithm for rate limiting."""

    def __init__(self, rate: float, capacity: float):
        self.rate = rate          # tokens per second
        self.capacity = capacity  # max burst
        self._tokens = capacity
        self._last = time.monotonic()
        self._lock = Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last = now

    def consume(self, tokens: float = 1.0) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def wait_and_consume(self, tokens: float = 1.0, timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.consume(tokens):
                return True
            time.sleep(0.01)
        return False

    @property
    def available(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens
