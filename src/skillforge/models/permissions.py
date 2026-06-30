from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Capability(str, Enum):
    network = "network"
    filesystem_read = "filesystem_read"
    filesystem_write = "filesystem_write"
    env_access = "env_access"
    dangerous = "dangerous"
    subprocess = "subprocess"
    audio = "audio"
    video = "video"
    camera = "camera"


class Permission(BaseModel):
    capability: Capability
    paths: list[str] = Field(default_factory=list)
    reason: str = ""


class PermissionSet(BaseModel):
    permissions: list[Permission] = Field(default_factory=list)
    allow_all: bool = False

    def has_capability(self, capability: Capability) -> bool:
        if self.allow_all:
            return True
        return any(p.capability == capability for p in self.permissions)

    def allowed_paths(self, capability: Capability) -> list[str]:
        if self.allow_all:
            return ["*"]
        return [p.paths for p in self.permissions if p.capability == capability][0] if any(
            p.capability == capability for p in self.permissions
        ) else []

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PermissionSet:
        return cls.model_validate(data)
