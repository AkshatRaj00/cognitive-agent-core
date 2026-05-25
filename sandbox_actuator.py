"""sandbox_actuator.py — Safe sandboxed execution with resource limits and timeout."""

import signal
import logging
import resource
import threading
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 10.0
_DEFAULT_MAX_MEMORY_MB = 256


class SandboxTimeoutError(Exception):
    """Raised when a sandboxed task exceeds its time limit."""


class SandboxMemoryError(Exception):
    """Raised when a sandboxed task exceeds its memory limit."""


class SandboxActuator:
    """Executes untrusted callables in a resource-limited sandbox.

    Limits enforced:
    - Wall-clock timeout via a daemon thread + threading.Event.
    - Virtual memory cap via resource.setrlimit (POSIX only).

    Note: Full process isolation requires running in a subprocess or
    container. This class provides a best-effort in-process guard
    suitable for trusted-but-potentially-expensive computations.
    """

    def __init__(
        self,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        max_memory_mb: int = _DEFAULT_MAX_MEMORY_MB,
        enable_memory_limit: bool = True,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.enable_memory_limit = enable_memory_limit

    def run(self, task: Callable[[], Any], task_name: str = "sandboxed_task") -> Any:
        """Execute *task* inside the sandbox.

        Args:
            task:       Zero-argument callable.
            task_name:  Label used in log / error messages.

        Returns:
            Whatever *task* returns.

        Raises:
            SandboxTimeoutError: If the task exceeds *timeout_seconds*.
            SandboxMemoryError:  If memory limit is breached (POSIX only).
            Exception:           Any exception raised by *task* itself.
        """
        if self.enable_memory_limit:
            self._apply_memory_limit()

        result_holder: list[Any] = [None]
        exception_holder: list[Optional[Exception]] = [None]
        done_event = threading.Event()

        def _runner() -> None:
            try:
                result_holder[0] = task()
            except MemoryError as exc:
                exception_holder[0] = SandboxMemoryError(str(exc))
            except Exception as exc:  # noqa: BLE001
                exception_holder[0] = exc
            finally:
                done_event.set()

        thread = threading.Thread(target=_runner, name=f"sandbox-{task_name}", daemon=True)
        thread.start()
        finished = done_event.wait(timeout=self.timeout_seconds)

        if not finished:
            logger.error("[%s] timed out after %.1fs", task_name, self.timeout_seconds)
            raise SandboxTimeoutError(
                f"{task_name} exceeded timeout of {self.timeout_seconds}s"
            )

        if exception_holder[0] is not None:
            raise exception_holder[0]

        return result_holder[0]

    def _apply_memory_limit(self) -> None:
        """Set virtual address space limit (POSIX only; silently skipped on Windows)."""
        try:
            limit_bytes = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        except (AttributeError, ValueError) as exc:
            logger.debug("Memory limit not applied: %s", exc)
