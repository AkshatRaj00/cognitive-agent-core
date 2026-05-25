"""config.py — Environment-aware configuration loader with validation."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    """Central configuration for the cognitive agent runtime."""

    # --- Model settings ---
    model_name: str = "gemini-1.5-pro"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    top_p: float = 0.95

    # --- Memory settings ---
    memory_ttl_seconds: Optional[float] = 3600.0   # 1 hour default
    memory_prune_interval: float = 120.0
    max_memory_entries: int = 1000

    # --- Runtime settings ---
    max_retries: int = 3
    retry_backoff_base: float = 1.5
    request_timeout_seconds: float = 30.0
    enable_telemetry: bool = True
    debug: bool = False

    # --- API keys (loaded from env, never hardcoded) ---
    gemini_api_key: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        """Validate config after initialisation."""
        if not self.gemini_api_key:
            self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

        errors: list[str] = []
        if not (0.0 <= self.temperature <= 2.0):
            errors.append(f"temperature must be in [0.0, 2.0], got {self.temperature}")
        if self.max_output_tokens <= 0:
            errors.append(f"max_output_tokens must be positive, got {self.max_output_tokens}")
        if self.max_retries < 0:
            errors.append(f"max_retries must be >= 0, got {self.max_retries}")
        if self.request_timeout_seconds <= 0:
            errors.append(f"request_timeout_seconds must be positive, got {self.request_timeout_seconds}")
        if errors:
            raise ValueError("AgentConfig validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


def load_config(**overrides) -> AgentConfig:
    """Build an AgentConfig, applying environment variables then keyword overrides.

    Environment variables (all prefixed ``AGENT_``):
        AGENT_MODEL_NAME, AGENT_TEMPERATURE, AGENT_MAX_OUTPUT_TOKENS,
        AGENT_MAX_RETRIES, AGENT_TIMEOUT, AGENT_DEBUG, AGENT_TELEMETRY

    Args:
        **overrides: Any AgentConfig field values to override last.

    Returns:
        Validated AgentConfig instance.
    """
    env_values: dict = {}

    if v := os.environ.get("AGENT_MODEL_NAME"):
        env_values["model_name"] = v
    if v := os.environ.get("AGENT_TEMPERATURE"):
        env_values["temperature"] = float(v)
    if v := os.environ.get("AGENT_MAX_OUTPUT_TOKENS"):
        env_values["max_output_tokens"] = int(v)
    if v := os.environ.get("AGENT_MAX_RETRIES"):
        env_values["max_retries"] = int(v)
    if v := os.environ.get("AGENT_TIMEOUT"):
        env_values["request_timeout_seconds"] = float(v)
    if v := os.environ.get("AGENT_DEBUG"):
        env_values["debug"] = v.lower() in ("1", "true", "yes")
    if v := os.environ.get("AGENT_TELEMETRY"):
        env_values["enable_telemetry"] = v.lower() in ("1", "true", "yes")

    return AgentConfig(**{**env_values, **overrides})
