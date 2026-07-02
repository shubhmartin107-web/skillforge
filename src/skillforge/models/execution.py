from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionMode(StrEnum):
    direct = "direct"
    tool_calling = "tool_calling"
    sub_agent = "sub_agent"


class ExecutionStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    timed_out = "timed_out"


class ExecutionRequest(BaseModel):
    skill_name: str
    skill_version: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    mode: ExecutionMode = ExecutionMode.direct
    timeout: int | None = None
    workflow_id: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    request: ExecutionRequest
    status: ExecutionStatus = ExecutionStatus.pending
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str | None = None

    @property
    def success(self) -> bool:
        return self.status == ExecutionStatus.completed

    @property
    def runtime_ms(self) -> int | None:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None
