"""cognitive_brain.py — CognitiveBrain with chain-of-thought reasoning and confidence scoring."""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

_COT_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL)
_CONFIDENCE_PATTERN = re.compile(r"confidence[:\s]+([0-9]*\.?[0-9]+)", re.IGNORECASE)


@dataclass
class ReasoningStep:
    """A single step in the chain-of-thought trace."""
    step_number: int
    thought: str
    conclusion: Optional[str] = None


@dataclass
class BrainResponse:
    """Structured output from CognitiveBrain.reason()."""
    raw_output: str
    final_answer: str
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)
    confidence: float = 1.0          # 0.0 – 1.0
    used_cot: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_confident(self, threshold: float = 0.6) -> bool:
        """Return True if confidence meets or exceeds *threshold*."""
        return self.confidence >= threshold


class CognitiveBrain:
    """Reasoning layer that parses chain-of-thought traces and scores confidence.

    The brain wraps raw LLM output and extracts:
    - ``<think>...</think>`` tagged reasoning steps
    - An inline confidence score (``confidence: 0.85``)
    - A clean final answer stripped of internal monologue

    This design is model-agnostic — any LLM that follows the prompt
    template can produce parseable output.
    """

    SYSTEM_PROMPT_TEMPLATE = (
        "You are a precise reasoning agent.\n"
        "When solving a problem:\n"
        "1. Wrap each reasoning step inside <think>...</think> tags.\n"
        "2. After all thinking, write your final answer on a new line prefixed with 'Answer:'.\n"
        "3. End with a confidence score like 'confidence: 0.85' (0.0 = unsure, 1.0 = certain).\n"
        "Be concise. Avoid unnecessary verbosity.\n"
    )

    def __init__(self, model_name: str = "gemini-1.5-pro") -> None:
        self.model_name = model_name

    def reason(self, prompt: str, raw_output: str) -> BrainResponse:
        """Parse *raw_output* from the LLM into a structured BrainResponse.

        Args:
            prompt:     The original user prompt (stored in metadata).
            raw_output: The full text returned by the LLM.

        Returns:
            BrainResponse with reasoning trace, answer, and confidence.
        """
        thoughts = _COT_PATTERN.findall(raw_output)
        steps = [
            ReasoningStep(step_number=i + 1, thought=t.strip())
            for i, t in enumerate(thoughts)
        ]

        # Extract final answer (everything after last </think> tag)
        cleaned = _COT_PATTERN.sub("", raw_output).strip()
        answer_match = re.search(r"(?:Answer:|A:)\s*(.*)", cleaned, re.IGNORECASE | re.DOTALL)
        final_answer = answer_match.group(1).strip() if answer_match else cleaned

        # Remove the trailing confidence line from the answer
        final_answer = _CONFIDENCE_PATTERN.sub("", final_answer).strip().rstrip(",;.")

        # Extract confidence
        conf_match = _CONFIDENCE_PATTERN.search(raw_output)
        confidence = float(conf_match.group(1)) if conf_match else 1.0
        confidence = max(0.0, min(1.0, confidence))   # clamp to [0, 1]

        response = BrainResponse(
            raw_output=raw_output,
            final_answer=final_answer,
            reasoning_steps=steps,
            confidence=confidence,
            used_cot=bool(steps),
            metadata={"prompt_len": len(prompt), "model": self.model_name},
        )

        logger.debug(
            "Brain parsed %d reasoning step(s), confidence=%.2f, cot=%s",
            len(steps), confidence, response.used_cot,
        )
        return response

    def build_prompt(self, user_message: str, context: Optional[str] = None) -> str:
        """Build the full prompt string including system instructions and optional context."""
        parts = [self.SYSTEM_PROMPT_TEMPLATE]
        if context:
            parts.append(f"Context:\n{context}\n")
        parts.append(f"User: {user_message}")
        return "\n".join(parts)

    @staticmethod
    def extract_entities(text: str) -> list[str]:
        """Very lightweight named-entity hint extraction (no ML dependency).

        Returns tokens that look like proper nouns (Title Case, 3+ chars).
        This is a heuristic only — replace with spaCy/NER in production.
        """
        tokens = re.findall(r"\b[A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*\b", text)
        # Deduplicate while preserving order
        seen: set[str] = set()
        result: list[str] = []
        for tok in tokens:
            if tok not in seen:
                seen.add(tok)
                result.append(tok)
        return result
