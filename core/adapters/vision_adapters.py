"""
Vision LLM Adapters for multi-modal CognitiveBrain.

Provides GeminiVisionAdapter and OpenAIVisionAdapter that accept
MultiModalInput and return text completions.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from core.types.multimodal import MultiModalInput

logger = logging.getLogger(__name__)


class BaseVisionAdapter(ABC):
    """Abstract base for vision-capable LLM adapters."""

    @abstractmethod
    async def complete(self, input: MultiModalInput, max_tokens: int = 1024) -> str:
        """Return a text completion for the given multi-modal input."""
        ...

    @abstractmethod
    def supports_images(self) -> bool:
        """Return True if this adapter supports image inputs."""
        ...


class GeminiVisionAdapter(BaseVisionAdapter):
    """
    Adapter for Google Gemini Vision API (gemini-1.5-flash / gemini-pro-vision).

    Requires ``google-generativeai`` package.
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.model = model

    def supports_images(self) -> bool:
        return True

    async def complete(self, input: MultiModalInput, max_tokens: int = 1024) -> str:
        try:
            import google.generativeai as genai  # optional
        except ImportError as exc:
            raise ImportError(
                "Install google-generativeai: pip install google-generativeai"
            ) from exc

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        parts = input.to_gemini_parts()

        logger.debug(
            "GeminiVision request: model=%s, text=%r, images=%d",
            self.model, input.text, len(input.images),
        )

        response = await model.generate_content_async(
            parts,
            generation_config={"max_output_tokens": max_tokens},
        )
        return response.text


class OpenAIVisionAdapter(BaseVisionAdapter):
    """
    Adapter for OpenAI GPT-4V / gpt-4o vision API.

    Requires ``openai`` package.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def supports_images(self) -> bool:
        return True

    async def complete(self, input: MultiModalInput, max_tokens: int = 1024) -> str:
        try:
            from openai import AsyncOpenAI  # optional
        except ImportError as exc:
            raise ImportError("Install openai: pip install openai") from exc

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        messages = input.to_openai_messages()

        logger.debug(
            "OpenAIVision request: model=%s, text=%r, images=%d",
            self.model, input.text, len(input.images),
        )

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
