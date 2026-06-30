from __future__ import annotations

from typing import Any

from skillforge.config import settings
from skillforge.runtime.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError("google-genai package required. Install with: pip install google-genai")
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> dict[str, Any]:
        client = self._get_client()
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        resp = client.models.generate_content(
            model=self.model,
            contents=contents,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                **kwargs,
            },
        )
        return {
            "content": resp.text if hasattr(resp, "text") else "",
            "model": self.model,
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
