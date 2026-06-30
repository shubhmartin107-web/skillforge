from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RegistryEntry(BaseModel):
    name: str
    version: str
    description: str = ""
    author_name: str = ""
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    installed_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    source: str = "local"
    source_url: str = ""
    manifest_path: str = ""
    skill_path: str = ""
    dependencies: list[str] = Field(default_factory=list)
    entrypoint: str = ""
    execution_mode: str = "direct"
    size_bytes: int = 0
    downloads: int = 0

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegistryEntry:
        return cls.model_validate(data)


class SearchQuery(BaseModel):
    query: str = ""
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    author: str = ""
    mode: str | None = None
    offset: int = 0
    limit: int = 50


class SearchResult(BaseModel):
    entries: list[RegistryEntry] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 50


class RegistryStats(BaseModel):
    total_skills: int = 0
    total_categories: int = 0
    total_tags: int = 0
    total_authors: int = 0
    last_updated: datetime | None = None
