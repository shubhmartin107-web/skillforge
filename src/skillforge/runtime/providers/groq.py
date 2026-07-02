from __future__ import annotations

from typing import Any

from skillforge.config import settings
from skillforge.runtime.providers.base import BaseProvider


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self, api_key: str | None = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or settings.groq_api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from groq import Groq

                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError("groq package required. Install with: pip install groq")
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> dict[str, Any]:
        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return {
            "content": resp.choices[0].message.content,
            "model": self.model,
            "usage": resp.usage.model_dump() if resp.usage else None,
        }

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        result = self.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return result.get("content", "")
