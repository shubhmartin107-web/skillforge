from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    skillforge_home: Path = Path.home() / ".skillforge"
    registry_db: str = "registry.db"
    skills_dir: str = "skills"
    cache_dir: str = "cache"
    logs_dir: str = "logs"
    audit_log: str = "audit.log"
    default_runtime: str = "python3.12"
    execution_timeout: int = 120
    max_memory_mb: int = 512
    sandbox_enabled: bool = True
    sandbox_mode: str = "auto"
    network_enabled: bool = False
    deepseek_api_key: str | None = None
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    log_level: str = "INFO"
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 7860
    server_api_keys: list[str] = []
    community_registry_url: str = "https://community.skillforge.ai"

    @field_validator("server_api_keys", mode="before")
    @classmethod
    def parse_server_api_keys(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                return json.loads(v)
            return [k.strip() for k in v.split(",") if k.strip()]
        return v or []

    @field_validator("sandbox_mode")
    @classmethod
    def validate_sandbox_mode(cls, v: str) -> str:
        allowed = {"auto", "wasm", "subprocess"}
        if v not in allowed:
            raise ValueError(f"sandbox_mode must be one of: {', '.join(allowed)}")
        return v

    @property
    def registry_path(self) -> Path:
        return self.skillforge_home / self.registry_db

    @property
    def skills_path(self) -> Path:
        return self.skillforge_home / self.skills_dir

    @property
    def cache_path(self) -> Path:
        return self.skillforge_home / self.cache_dir

    @property
    def logs_path(self) -> Path:
        return self.skillforge_home / self.logs_dir

    @property
    def audit_path(self) -> Path:
        return self.logs_path / self.audit_log

    def ensure_dirs(self) -> None:
        self.skillforge_home.mkdir(parents=True, exist_ok=True)
        self.skills_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

    model_config = {"env_prefix": "SKILLFORGE_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
