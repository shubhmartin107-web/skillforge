from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from skillforge.config import settings

logger = logging.getLogger("skillforge.audit")


class AuditLogger:
    def __init__(self, log_path: Path | None = None):
        self.log_path = log_path or settings.audit_path

    def log(
        self,
        event: str,
        skill_name: str,
        actor: str = "system",
        details: dict | None = None,
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "skill_name": skill_name,
            "actor": actor,
            "details": details or {},
        }

        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def log_execution(
        self,
        skill_name: str,
        status: str,
        duration_ms: int | None = None,
        inputs: dict | None = None,
        outputs: dict | None = None,
        error: str | None = None,
    ) -> None:
        self.log(
            event="skill.execution",
            skill_name=skill_name,
            details={
                "status": status,
                "duration_ms": duration_ms,
                "inputs": self._sanitize(inputs or {}),
                "outputs": self._sanitize(outputs or {}),
                "error": error,
            },
        )

    def log_install(self, skill_name: str, version: str, source: str) -> None:
        self.log(
            event="skill.install",
            skill_name=skill_name,
            details={"version": version, "source": source},
        )

    def log_remove(self, skill_name: str, version: str | None) -> None:
        self.log(
            event="skill.remove",
            skill_name=skill_name,
            details={"version": version},
        )

    def _sanitize(self, data: dict) -> dict:
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in ("key", "secret", "password", "token", "auth")):
                sanitized[key] = "***"
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + "..."
            else:
                sanitized[key] = value
        return sanitized

    def get_recent(self, limit: int = 50) -> list[dict]:
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries[-limit:]
