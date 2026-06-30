from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import yaml

from skillforge.config import settings
from skillforge.models.registry import RegistryEntry
from skillforge.models.skill import SkillManifest, SkillDependency
from skillforge.registry.local import LocalRegistry
from skillforge.registry.resolver import DependencyResolver


class InstallError(Exception):
    pass


class Installer:
    def __init__(self, registry: LocalRegistry | None = None):
        self.registry = registry or LocalRegistry()
        self.resolver = DependencyResolver(self.registry)

    def install_from_path(self, source_path: Path) -> RegistryEntry:
        source_path = Path(source_path).resolve()
        if not source_path.exists():
            raise InstallError(f"Source path does not exist: {source_path}")

        manifest = self._load_manifest(source_path)
        self._validate_manifest(manifest)

        existing = self.registry.get(manifest.name, manifest.version)
        if existing:
            raise InstallError(
                f"Skill '{manifest.name}@{manifest.version}' already installed. "
                "Use update() or remove first."
            )

        self._resolve_dependencies(manifest.dependencies)

        dest = settings.skills_path / manifest.name / manifest.version
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if source_path.is_file():
            shutil.copy2(source_path, dest / "skill.yaml")
        else:
            self._copy_skill_dir(source_path, dest)

        size_bytes = self._dir_size(dest)
        entry = RegistryEntry(
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author_name=manifest.author.name,
            tags=manifest.tags,
            categories=manifest.categories,
            source="local",
            manifest_path=str(dest / "skill.yaml"),
            skill_path=str(dest),
            dependencies=[d.name for d in manifest.dependencies],
            entrypoint=manifest.execution.get("entrypoint", "skill.py"),
            execution_mode=manifest.execution.get("mode", "direct"),
            size_bytes=size_bytes,
        )
        self.registry.install(entry)
        return entry

    def remove(self, name: str, version: str | None = None) -> bool:
        entry = self.registry.get(name, version)
        if entry is None:
            return False

        skill_dir = Path(entry.skill_path)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)

        parent = skill_dir.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()

        return self.registry.remove(name, version)

    def update(self, name: str, source_path: Path | None = None) -> RegistryEntry | None:
        current = self.registry.get(name)
        if current is None:
            raise InstallError(f"Skill '{name}' is not installed")

        if source_path:
            manifest = self._load_manifest(source_path)
        else:
            skill_dir = Path(current.skill_path)
            if not skill_dir.exists():
                raise InstallError(f"Skill directory not found: {current.skill_path}")
            manifest = self._load_manifest(skill_dir)

        if manifest.version == current.version:
            return self.install_from_path(source_path or Path(current.skill_path))

        self.registry.remove(name, current.version)
        return self.install_from_path(source_path or Path(current.skill_path))

    def _load_manifest(self, path: Path) -> SkillManifest:
        path = Path(path)
        if path.is_dir():
            for fname in ("skill.yaml", "skill.yml", "skill.json"):
                fpath = path / fname
                if fpath.exists():
                    return self._parse_manifest(fpath)
            raise InstallError(f"No skill manifest found in {path}")
        else:
            return self._parse_manifest(path)

    def _parse_manifest(self, path: Path) -> SkillManifest:
        content = path.read_text("utf-8")
        if path.suffix == ".json":
            data = json.loads(content)
        else:
            data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise InstallError("Invalid manifest format")
        return SkillManifest.from_yaml_dict(data)

    def _validate_manifest(self, manifest: SkillManifest) -> None:
        if not manifest.name:
            raise InstallError("Skill name is required")
        if not manifest.version:
            raise InstallError("Skill version is required")

    def _resolve_dependencies(self, dependencies: list[SkillDependency]) -> None:
        resolved = self.resolver.resolve(dependencies)
        for dep_name, dep_version in resolved.items():
            existing = self.registry.get(dep_name)
            if existing is None:
                raise InstallError(
                    f"Required dependency '{dep_name}@{dep_version}' is not installed"
                )

    def _copy_skill_dir(self, src: Path, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            s = src / item.name
            d = dest / item.name
            if s.is_dir():
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    def _dir_size(self, path: Path) -> int:
        total = 0
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total
