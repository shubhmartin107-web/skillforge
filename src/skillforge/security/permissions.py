from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from skillforge.models.skill import Permission


class PermissionError(Exception):
    pass


class IntegrityError(Exception):
    pass


class PermissionValidator:
    def __init__(self, manifest_permissions: Permission | None = None):
        self.permissions = manifest_permissions or Permission()

    def check_network(self) -> bool:
        if not self.permissions.network:
            raise PermissionError("Skill does not have network permission")
        return True

    def check_file_read(self, path: str) -> bool:
        if not self.permissions.filesystem_read:
            raise PermissionError("Skill does not have filesystem read permission")
        allowed = self.permissions.filesystem_read
        if "*" in allowed:
            return True
        path_obj = Path(path).resolve()
        for allowed_path in allowed:
            allowed_obj = Path(allowed_path).resolve()
            if allowed_obj in path_obj.parents or allowed_obj == path_obj:
                return True
        raise PermissionError(f"Read access denied to '{path}'")

    def check_file_write(self, path: str) -> bool:
        if not self.permissions.filesystem_write:
            raise PermissionError("Skill does not have filesystem write permission")
        allowed = self.permissions.filesystem_write
        if "*" in allowed:
            return True
        path_obj = Path(path).resolve()
        for allowed_path in allowed:
            allowed_obj = Path(allowed_path).resolve()
            if allowed_obj in path_obj.parents or allowed_obj == path_obj:
                return True
        raise PermissionError(f"Write access denied to '{path}'")

    def check_env_var(self, var_name: str) -> bool:
        if var_name not in self.permissions.env_vars:
            raise PermissionError(f"Access denied to environment variable '{var_name}'")
        return True

    def check_dangerous(self) -> bool:
        if not self.permissions.dangerous:
            raise PermissionError("Skill does not have dangerous capability permission")
        return True

    def validate_all(self, requested: dict[str, Any]) -> None:
        for action, target in requested.items():
            if action == "network":
                self.check_network()
            elif action == "file_read":
                self.check_file_read(target)
            elif action == "file_write":
                self.check_file_write(target)
            elif action == "env_var":
                self.check_env_var(target)
            elif action == "dangerous":
                self.check_dangerous()


def verify_skill_integrity(skill_path: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for file_path in sorted(skill_path.rglob("*")):
        if file_path.is_file() and file_path.name != "checksums.txt":
            content = file_path.read_bytes()
            h = hashlib.sha256(content).hexdigest()
            rel = str(file_path.relative_to(skill_path))
            hashes[rel] = h
    return hashes


def verify_against_checksums(skill_path: Path, checksums: dict[str, str]) -> bool:
    current = verify_skill_integrity(skill_path)
    for rel_path, expected_hash in checksums.items():
        actual = current.get(rel_path)
        if actual is None:
            raise IntegrityError(f"Missing file: {rel_path}")
        if actual != expected_hash:
            raise IntegrityError(
                f"Integrity check failed for '{rel_path}': expected {expected_hash}, got {actual}"
            )
    return True


def generate_checksums_file(skill_path: Path) -> str:
    hashes = verify_skill_integrity(skill_path)
    lines = [f"{h}  {p}" for p, h in sorted(hashes.items())]
    return "\n".join(lines)
