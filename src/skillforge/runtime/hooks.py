from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from skillforge.config import settings

logger = logging.getLogger("skillforge")


class ExecutionHooks:
    def __init__(self, trace_id: str | None = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self._start_time: float | None = None
        self._events: list[dict[str, Any]] = []
        self._listeners: dict[str, list[Callable]] = {
            "skill.started": [],
            "skill.completed": [],
            "skill.failed": [],
            "skill.output": [],
            "workflow.started": [],
            "workflow.completed": [],
            "workflow.failed": [],
        }

    def on(self, event: str, callback: Callable) -> None:
        if event in self._listeners:
            self._listeners[event].append(callback)

    def emit(self, event: str, data: dict[str, Any]) -> None:
        timestamp = datetime.now().isoformat()
        payload = {
            "event": event,
            "trace_id": self.trace_id,
            "timestamp": timestamp,
            "data": data,
        }
        self._events.append(payload)

        for listener in self._listeners.get(event, []):
            try:
                listener(payload)
            except Exception as e:
                logger.warning(f"Hook listener failed for {event}: {e}")

        self._log_event(payload)

    def start(self, **kwargs: Any) -> None:
        self._start_time = time.time()
        self.emit("skill.started", {"started_at": datetime.now().isoformat(), **kwargs})

    def complete(self, **kwargs: Any) -> None:
        duration = None
        if self._start_time:
            duration = int((time.time() - self._start_time) * 1000)
        self.emit("skill.completed", {"duration_ms": duration, **kwargs})

    def fail(self, error: str, **kwargs: Any) -> None:
        self.emit("skill.failed", {"error": error, **kwargs})

    def output(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        self.emit("skill.output", {"outputs": outputs, **kwargs})

    def get_events(self) -> list[dict[str, Any]]:
        return list(self._events)

    def to_flowlens(self) -> list[dict[str, Any]]:
        spans = []
        for event in self._events:
            span = {
                "trace_id": event["trace_id"],
                "span_id": str(uuid.uuid4()),
                "name": event["event"],
                "timestamp": event["timestamp"],
                "attributes": event["data"],
            }
            spans.append(span)
        return spans

    def _log_event(self, event: dict[str, Any]) -> None:
        try:
            log_path = settings.audit_path
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.debug(f"Failed to write audit log: {e}")
