"""
Multi-modal input types for CognitiveBrain.

Adds image + text input support so the brain can process
visual context alongside natural language queries.
"""
from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Union


@dataclass
class TextInput:
    """Plain text input."""
    content: str
    role: Literal["user", "system", "assistant"] = "user"


@dataclass
class ImageInput:
    """
    Image input for vision-capable LLMs.

    Accepts raw bytes or a file path. Converts to base64 on demand.
    """
    source: Union[bytes, str, Path]
    mime_type: Optional[str] = None
    caption: Optional[str] = None
    _b64_cache: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if isinstance(self.source, (str, Path)):
            path = Path(self.source)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {path}")
            if self.mime_type is None:
                guessed, _ = mimetypes.guess_type(str(path))
                self.mime_type = guessed or "image/jpeg"

    @property
    def base64_data(self) -> str:
        """Return base64-encoded image data (cached after first call)."""
        if self._b64_cache is None:
            if isinstance(self.source, bytes):
                raw = self.source
            else:
                raw = Path(self.source).read_bytes()
            self._b64_cache = base64.b64encode(raw).decode("utf-8")
        return self._b64_cache

    @property
    def data_uri(self) -> str:
        """Return a data URI suitable for embedding in HTML or API payloads."""
        mime = self.mime_type or "image/jpeg"
        return f"data:{mime};base64,{self.base64_data}"

    def to_api_payload(self) -> dict:
        """Convert to the payload format expected by vision LLM APIs."""
        return {
            "type": "image_url",
            "image_url": {"url": self.data_uri},
        }


@dataclass
class MultiModalInput:
    """
    Combined text + image input for multi-modal brain queries.

    Example::

        img = ImageInput(source="/path/to/chart.png", caption="Q3 revenue chart")
        query = MultiModalInput(
            text="What trend do you see in this chart?",
            images=[img],
        )
        brain.think(query)
    """
    text: str
    images: list[ImageInput] = field(default_factory=list)
    role: Literal["user", "system"] = "user"

    def to_openai_messages(self) -> list[dict]:
        """Convert to OpenAI chat completion messages format."""
        content: list[dict] = [{"type": "text", "text": self.text}]
        for img in self.images:
            content.append(img.to_api_payload())
            if img.caption:
                content.append({"type": "text", "text": f"Caption: {img.caption}"})
        return [{"role": self.role, "content": content}]

    def to_gemini_parts(self) -> list[dict]:
        """Convert to Gemini Vision API parts format."""
        parts: list[dict] = [{"text": self.text}]
        for img in self.images:
            parts.append({
                "inline_data": {
                    "mime_type": img.mime_type or "image/jpeg",
                    "data": img.base64_data,
                }
            })
        return parts


# Union type accepted by CognitiveBrain.think()
AgentInput = Union[str, TextInput, MultiModalInput]
