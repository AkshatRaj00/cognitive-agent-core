"""pipeline.py — Multi-step AgentPipeline with hooks and dry-run support."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Outcome of a single pipeline step."""
    name: str
    success: bool
    output: Any = None
    error: Optional[Exception] = None
    elapsed_ms: float = 0.0

    def raise_if_failed(self) -> None:
        if not self.success and self.error:
            raise self.error


@dataclass
class PipelineRun:
    """Complete result of one pipeline execution."""
    steps: list[StepResult] = field(default_factory=list)
    aborted: bool = False

    @property
    def succeeded(self) -> bool:
        return not self.aborted and all(s.success for s in self.steps)

    @property
    def final_output(self) -> Any:
        """Output of the last successful step."""
        for s in reversed(self.steps):
            if s.success:
                return s.output
        return None


Step = Callable[[Any], Any]
Hook = Callable[[StepResult], None]


class AgentPipeline:
    """Composable pipeline that chains agent steps sequentially.

    Each step receives the output of the previous step as its input.
    On failure the pipeline can either abort or continue depending on
    the ``fail_fast`` setting.

    Example::

        pipeline = AgentPipeline(fail_fast=True)
        pipeline.add_step("tokenise", tokenise_fn)
        pipeline.add_step("classify", classify_fn)
        pipeline.add_step("respond", respond_fn)

        result = pipeline.run(user_input)
        print(result.final_output)
    """

    def __init__(
        self,
        *,
        fail_fast: bool = True,
        dry_run: bool = False,
    ) -> None:
        self.fail_fast = fail_fast
        self.dry_run = dry_run
        self._steps: list[tuple[str, Step]] = []
        self._before_hooks: list[Hook] = []
        self._after_hooks: list[Hook] = []

    # ------------------------------------------------------------------
    # Builder API
    # ------------------------------------------------------------------

    def add_step(self, name: str, fn: Step) -> "AgentPipeline":
        """Append a named step. Returns self for chaining."""
        self._steps.append((name, fn))
        return self

    def on_step_start(self, hook: Hook) -> "AgentPipeline":
        """Register a hook called before each step executes."""
        self._before_hooks.append(hook)
        return self

    def on_step_end(self, hook: Hook) -> "AgentPipeline":
        """Register a hook called after each step completes (or fails)."""
        self._after_hooks.append(hook)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, initial_input: Any = None) -> PipelineRun:
        """Execute all steps in order."""
        run = PipelineRun()
        current = initial_input

        for name, fn in self._steps:
            if self.dry_run:
                logger.info("[dry-run] step '%s' skipped", name)
                run.steps.append(StepResult(name=name, success=True, output=current))
                continue

            start = time.perf_counter()
            try:
                output = fn(current)
                elapsed = (time.perf_counter() - start) * 1000
                result = StepResult(name=name, success=True, output=output, elapsed_ms=elapsed)
                logger.debug("Step '%s' OK (%.1f ms)", name, elapsed)
            except Exception as exc:  # noqa: BLE001
                elapsed = (time.perf_counter() - start) * 1000
                result = StepResult(name=name, success=False, error=exc, elapsed_ms=elapsed)
                logger.warning("Step '%s' FAILED: %s", name, exc)

            # Run hooks
            for hook in self._before_hooks if not result.success else self._after_hooks:
                try:
                    hook(result)
                except Exception:  # noqa: BLE001
                    pass
            for hook in self._after_hooks:
                try:
                    hook(result)
                except Exception:  # noqa: BLE001
                    pass

            run.steps.append(result)

            if not result.success and self.fail_fast:
                run.aborted = True
                logger.error("Pipeline aborted at step '%s'.", name)
                break

            current = result.output

        logger.info(
            "Pipeline finished: %d/%d steps succeeded, aborted=%s",
            sum(1 for s in run.steps if s.success),
            len(run.steps),
            run.aborted,
        )
        return run

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def step_names(self) -> list[str]:
        """Return ordered list of step names."""
        return [name for name, _ in self._steps]

    def __repr__(self) -> str:
        return (
            f"AgentPipeline(steps={self.step_names()}, "
            f"fail_fast={self.fail_fast}, dry_run={self.dry_run})"
        )
