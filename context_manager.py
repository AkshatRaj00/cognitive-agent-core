"""context_manager.py — Hierarchical ContextManager for agent conversation state."""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Turn:
    """A single conversational turn (user + assistant)."""
    role: str           # 'user' | 'assistant' | 'system'
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """Manages conversational context for an agent session.

    Maintains a sliding window of recent turns, enforces a token budget,
    and supports context injection (system prompts, retrieved docs, etc.).

    Args:
        max_turns:      Maximum turns kept in the active window.
        max_tokens:     Soft token budget (characters / 4 approximation).
        session_id:     Optional label for this context window.
    """

    CHARS_PER_TOKEN = 4   # rough heuristic

    def __init__(
        self,
        max_turns: int = 20,
        max_tokens: int = 8_000,
        session_id: Optional[str] = None,
    ) -> None:
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.session_id = session_id or "default"
        self._history: deque[Turn] = deque(maxlen=max_turns)
        self._injections: list[Turn] = []   # system/doc injections, always prepended

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def add_turn(self, role: str, content: str, **meta: Any) -> Turn:
        """Append a turn to the history window."""
        turn = Turn(role=role, content=content, metadata=meta)
        self._history.append(turn)
        logger.debug("Context turn added: role=%s, tokens~=%d", role, self._estimate_tokens(content))
        return turn

    def inject(self, content: str, label: str = "system") -> None:
        """Prepend persistent context (system prompt, RAG chunks, etc.)."""
        self._injections.append(Turn(role="system", content=content, metadata={"label": label}))

    def clear_history(self) -> None:
        """Wipe the sliding window but keep injections."""
        self._history.clear()

    def clear_all(self) -> None:
        """Wipe everything including injections."""
        self._history.clear()
        self._injections.clear()

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def build_messages(self) -> list[dict[str, str]]:
        """Return the full context as a list of {role, content} dicts.

        Injections come first; history follows in chronological order.
        Automatically trims history to stay within the token budget.
        """
        messages = [{"role": t.role, "content": t.content} for t in self._injections]
        trimmed = self._trim_to_budget(list(self._history))
        messages += [{"role": t.role, "content": t.content} for t in trimmed]
        return messages

    def last_user_message(self) -> Optional[str]:
        """Return the most recent user turn content, or None."""
        for turn in reversed(self._history):
            if turn.role == "user":
                return turn.content
        return None

    @property
    def total_tokens(self) -> int:
        """Estimated token count of the current context window."""
        all_text = " ".join(t.content for t in [*self._injections, *self._history])
        return self._estimate_tokens(all_text)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // self.CHARS_PER_TOKEN)

    def _trim_to_budget(self, turns: list[Turn]) -> list[Turn]:
        injection_tokens = sum(
            self._estimate_tokens(t.content) for t in self._injections
        )
        budget = self.max_tokens - injection_tokens
        result: list[Turn] = []
        running = 0
        for turn in reversed(turns):
            cost = self._estimate_tokens(turn.content)
            if running + cost > budget:
                break
            result.append(turn)
            running += cost
        return list(reversed(result))

    def __len__(self) -> int:
        return len(self._history)

    def __repr__(self) -> str:
        return (
            f"ContextManager(session={self.session_id!r}, "
            f"turns={len(self)}, tokens~={self.total_tokens})"
        )
