from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from semver import Version


class ExecutionMode(StrEnum):
    direct = "direct"
    tool_calling = "tool_calling"
    sub_agent = "sub_agent"


class SkillInput(BaseModel):
    name: str
    type: str = Field(description="Type name: string, integer, float, boolean, list, object")
    description: str = ""
    required: bool = True
    default: Any = None
    sensitive: bool = Field(default=False, description="Mark as sensitive (e.g. API keys)")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"string", "integer", "float", "boolean", "list", "object", "any"}
        if v not in allowed:
            raise ValueError(f"Invalid type '{v}'. Must be one of: {', '.join(sorted(allowed))}")
        return v


class SkillOutput(BaseModel):
    name: str
    type: str = "any"
    description: str = ""


class SkillAuthor(BaseModel):
    name: str = "Unknown"
    contact: str = ""


class SkillDependency(BaseModel):
    name: str
    version: str = "*"
    source: str = "builtins"


class Permission(BaseModel):
    network: bool = False
    filesystem_read: list[str] = Field(default_factory=list)
    filesystem_write: list[str] = Field(default_factory=list)
    env_vars: list[str] = Field(default_factory=list)
    dangerous: bool = False


class SkillManifest(BaseModel):
    schema_version: str = "1.0"
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: SkillAuthor = Field(default_factory=SkillAuthor)
    inputs: list[SkillInput] = Field(default_factory=list)
    outputs: list[SkillOutput] = Field(default_factory=list)
    dependencies: list[SkillDependency] = Field(default_factory=list)
    permissions: Permission = Field(default_factory=Permission)
    execution: dict[str, Any] = Field(
        default_factory=lambda: {
            "mode": "direct",
            "entrypoint": "skill.py",
            "function": "run",
            "runtime": "python3.12",
        }
    )
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    license: str = ""
    documentation: str = ""
    examples: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        try:
            Version.parse(v)
        except ValueError as e:
            raise ValueError(f"Invalid semantic version '{v}': {e}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 128:
            raise ValueError("Skill name must be 1-128 characters")
        if not v[0].isalnum():
            raise ValueError("Skill name must start with an alphanumeric character")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
        if not all(c in allowed for c in v):
            raise ValueError(
                "Skill name may only contain alphanumerics, hyphens, underscores, and dots"
            )
        return v

    def to_yaml_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True, by_alias=True)

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> SkillManifest:
        return cls.model_validate(data)
