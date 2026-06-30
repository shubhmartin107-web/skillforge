from __future__ import annotations

from typing import Any

import httpx

from skillforge.config import settings
from skillforge.runtime.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str = "llama3.2"):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(base_url=self.base_url, timeout=120.0)
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> dict[str, Any]:
        client = self._get_client()
        resp = client.post("/api/chat", json={
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs,
            },
            "stream": False,
        })
        resp.raise_for_status()
        data = resp.json()
        return {
            "content": data.get("message", {}).get("content", ""),
            "model": self.model,
            "usage": None,
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

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
