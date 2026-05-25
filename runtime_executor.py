"""runtime_executor.py — Executes agent tasks with retry and backoff."""

import time
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Raised when an agent task fails after all retry attempts."""

    def __init__(self, message: str, attempts: int, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


class RuntimeExecutor:
    """Executes callable tasks with configurable retry and exponential backoff.

    Attributes:
        max_retries:   Maximum number of retry attempts (0 means try once only).
        backoff_base:  Multiplier for backoff delay between retries.
        timeout:       Per-attempt timeout in seconds (not enforced internally;
                       callers should wrap with concurrent.futures if needed).
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 1.5,
        timeout: float = 30.0,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.timeout = timeout
        self.retryable_exceptions = retryable_exceptions

    def execute(self, task: Callable[[], Any], task_name: str = "task") -> Any:
        """Run *task* with retry logic.

        Args:
            task:       Zero-argument callable to execute.
            task_name:  Human-readable name used in log messages.

        Returns:
            The return value of *task* on success.

        Raises:
            ExecutionError: When all attempts are exhausted.
        """
        last_exc: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug("[%s] attempt %d/%d", task_name, attempt + 1, self.max_retries + 1)
                result = task()
                if attempt > 0:
                    logger.info("[%s] succeeded on attempt %d", task_name, attempt + 1)
                return result

            except self.retryable_exceptions as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < self.max_retries:
                    delay = self.backoff_base ** attempt
                    logger.warning(
                        "[%s] attempt %d failed (%s), retrying in %.2fs",
                        task_name, attempt + 1, exc, delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "[%s] all %d attempts failed. Last error: %s",
                        task_name, self.max_retries + 1, exc,
                    )

        raise ExecutionError(
            f"{task_name} failed after {self.max_retries + 1} attempt(s)",
            attempts=self.max_retries + 1,
            last_exception=last_exc,
        )

    def execute_with_fallback(self, task: Callable[[], Any], fallback: Any, task_name: str = "task") -> Any:
        """Like execute(), but returns *fallback* instead of raising on total failure."""
        try:
            return self.execute(task, task_name=task_name)
        except ExecutionError:
            logger.warning("[%s] using fallback value after all retries exhausted", task_name)
            return fallback
