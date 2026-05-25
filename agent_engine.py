"""agent_engine.py — Main AgentEngine with streaming response support."""

import logging
from typing import Any, Generator, Optional
from config import AgentConfig, load_config
from memory_store import MemoryStore
from core_telemetry import Telemetry
from runtime_executor import RuntimeExecutor
from master_orchestrator import MasterOrchestrator

logger = logging.getLogger(__name__)


class AgentEngine:
    """Central agent runtime wiring all subsystems together.

    Supports both synchronous and streaming LLM response modes.
    """

    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self.config = config or load_config()
        self.memory = MemoryStore(
            default_ttl=self.config.memory_ttl_seconds,
            prune_interval=self.config.memory_prune_interval,
        )
        self.telemetry = Telemetry(
            max_events=500,
            enabled=self.config.enable_telemetry,
        )
        self.executor = RuntimeExecutor(
            max_retries=self.config.max_retries,
            backoff_base=self.config.retry_backoff_base,
            timeout=self.config.request_timeout_seconds,
        )
        self.orchestrator = MasterOrchestrator(
            on_task_start=lambda name: self.telemetry.record("task.start", metadata={"name": name}),
            on_task_success=lambda name, _: self.telemetry.record("task.success", metadata={"name": name}),
            on_task_error=lambda name, exc: self.telemetry.record(
                "task.error", success=False, error=str(exc), metadata={"name": name}
            ),
        )
        self._session_id: Optional[str] = None
        logger.info("AgentEngine initialised with model=%s", self.config.model_name)

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def start_session(self, session_id: str) -> None:
        """Begin a new agent session, clearing stale session memory."""
        self._session_id = session_id
        self.memory.set(f"session:{session_id}:active", True, ttl=3600)
        self.telemetry.record("session.start", metadata={"session_id": session_id})
        logger.info("Session started: %s", session_id)

    def end_session(self) -> None:
        """Gracefully close the current session."""
        if self._session_id:
            self.telemetry.record("session.end", metadata={"session_id": self._session_id})
            self._session_id = None
        self.memory.shutdown()

    # ------------------------------------------------------------------
    # Core inference
    # ------------------------------------------------------------------

    def run(self, prompt: str, *, stream: bool = False) -> Any:
        """Execute a prompt through the agent pipeline.

        Args:
            prompt: User input / task description.
            stream: If True, returns a generator yielding text chunks.

        Returns:
            Full response string (stream=False) or a text-chunk generator.
        """
        with self.telemetry.timed("agent.run", metadata={"stream": stream, "prompt_len": len(prompt)}):
            if stream:
                return self._stream(prompt)
            return self.executor.execute(
                lambda: self._call_model(prompt),
                task_name="agent.run",
            )

    def _call_model(self, prompt: str) -> str:
        """Placeholder for LLM call — replace with Gemini SDK call."""
        # In production: use google.generativeai.GenerativeModel.generate_content()
        logger.debug("Calling model %s with prompt (len=%d)", self.config.model_name, len(prompt))
        return f"[{self.config.model_name}] Response to: {prompt[:80]}"

    def _stream(self, prompt: str) -> Generator[str, None, None]:
        """Yield response text chunks for streaming display."""
        # In production: use stream=True in Gemini SDK and yield chunk.text
        response = self._call_model(prompt)
        for word in response.split():
            yield word + " "

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def remember(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value in the agent's memory."""
        self.memory.set(key, value, ttl=ttl)

    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the agent's memory."""
        return self.memory.get(key, default)

    def status(self) -> dict[str, Any]:
        """Return a dict summarising the current agent state."""
        return {
            "session_id": self._session_id,
            "model": self.config.model_name,
            "memory_entries": len(self.memory),
            "pending_tasks": self.orchestrator.pending_count,
            "telemetry": self.telemetry.summary(),
        }
