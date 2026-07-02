from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str: ...

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ):
        raise NotImplementedError(f"{self.name} does not support streaming")

    def to_tool_json(
        self, skill_name: str, description: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": skill_name,
                "description": description,
                "parameters": parameters,
            },
        }
