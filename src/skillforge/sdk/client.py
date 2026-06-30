from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from skillforge.models.execution import ExecutionMode, ExecutionRequest, ExecutionResult
from skillforge.models.registry import RegistryEntry, SearchQuery, SearchResult
from skillforge.models.skill import SkillInput, SkillManifest
from skillforge.registry.installer import Installer
from skillforge.registry.local import LocalRegistry
from skillforge.runtime.executor import Executor
from skillforge.runtime.hooks import ExecutionHooks


class Forge:
    def __init__(self, registry: LocalRegistry | None = None):
        self.registry = registry or LocalRegistry()
        self._installer: Installer | None = None
        self._executor: Executor | None = None

    @property
    def installer(self) -> Installer:
        if self._installer is None:
            self._installer = Installer(registry=self.registry)
        return self._installer

    @property
    def executor(self) -> Executor:
        if self._executor is None:
            self._executor = Executor(registry=self.registry)
        return self._executor

    # ---- Registry Operations ----

    def install(self, source: str | Path) -> RegistryEntry:
        return self.installer.install_from_path(Path(source))

    def remove(self, name: str, version: str | None = None) -> bool:
        return self.installer.remove(name, version)

    def list_skills(self) -> list[RegistryEntry]:
        return self.registry.list_all()

    def search(self, query: str = "", tags: list[str] | None = None, category: str = "") -> SearchResult:
        q = SearchQuery(query=query, tags=tags or [])
        if category:
            q.categories = [category]
        return self.registry.search(q)

    def get_skill(self, name: str, version: str | None = None) -> RegistryEntry | None:
        return self.registry.get(name, version)

    def get_skill_manifest(self, name: str) -> SkillManifest | None:
        import yaml
        entry = self.registry.get(name)
        if entry is None:
            return None
        manifest_path = Path(entry.manifest_path)
        if not manifest_path.exists():
            return None
        raw = yaml.safe_load(manifest_path.read_text("utf-8"))
        return SkillManifest.from_yaml_dict(raw)

    # ---- Execution Operations ----

    def run(
        self,
        skill_name: str,
        *,
        version: str | None = None,
        mode: ExecutionMode = ExecutionMode.direct,
        sandbox: bool = False,
        hooks: ExecutionHooks | None = None,
        timeout: int | None = None,
        **inputs: Any,
    ) -> ExecutionResult:
        request = ExecutionRequest(
            skill_name=skill_name,
            skill_version=version,
            inputs=inputs,
            mode=mode,
            timeout=timeout,
            trace_id=hooks.trace_id if hooks else None,
        )

        if sandbox:
            return self.executor.execute_in_sandbox(request, hooks=hooks)
        return self.executor.execute(request, hooks=hooks)

    async def run_async(
        self,
        skill_name: str,
        *,
        version: str | None = None,
        mode: ExecutionMode = ExecutionMode.direct,
        sandbox: bool = False,
        **inputs: Any,
    ) -> ExecutionResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.run(
                skill_name,
                version=version,
                mode=mode,
                sandbox=sandbox,
                **inputs,
            ),
        )

    # ---- Inline Skill Registration ----

    def register_skill(
        self,
        name: str,
        version: str = "0.1.0",
        description: str = "",
        inputs: list[SkillInput] | None = None,
        network: bool = False,
        tags: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> _SkillRegistrar:
        return _SkillRegistrar(
            forge=self,
            name=name,
            version=version,
            description=description,
            inputs=inputs or [],
            network=network,
            tags=tags or [],
            categories=categories or [],
        )

    # ---- Utilities ----

    def create_skill(self, name: str, path: str | None = None) -> Path:
        from skillforge.cli.skill_cmds import _create_skill_files
        dest = Path(path or Path.cwd() / name)
        _create_skill_files(dest, name)
        return dest

    def validate_manifest(self, path: str | Path) -> SkillManifest:
        import yaml
        p = Path(path)
        content = p.read_text("utf-8")
        data = yaml.safe_load(content)
        return SkillManifest.from_yaml_dict(data)

    def stats(self):
        return self.registry.stats()

    def close(self):
        self.registry.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class _SkillRegistrar:
    def __init__(
        self,
        forge: Forge,
        name: str,
        version: str,
        description: str,
        inputs: list[SkillInput],
        network: bool = False,
        tags: list[str] | None = None,
        categories: list[str] | None = None,
    ):
        self.forge = forge
        self.name = name
        self.version = version
        self.description = description
        self.inputs = inputs
        self.network = network
        self.tags = tags or []
        self.categories = categories or []

    def __call__(self, func):
        import inspect
        import tempfile

        manifest = SkillManifest(
            name=self.name,
            version=self.version,
            description=self.description or func.__doc__ or "",
            inputs=self.inputs,
            outputs=[],
            permissions={
                "network": self.network,
                "filesystem_read": [],
                "filesystem_write": [],
                "env_vars": [],
                "dangerous": False,
            },
            execution={
                "mode": "direct",
                "entrypoint": "skill.py",
                "function": func.__name__,
                "runtime": "python3.12",
            },
            tags=self.tags,
            categories=self.categories,
        )

        tmp = Path(tempfile.mkdtemp(prefix="skillforge_inline_"))
        import yaml
        (tmp / "skill.yaml").write_text(yaml.dump(manifest.to_yaml_dict(), default_flow_style=False))
        import re
        import textwrap
        try:
            source = textwrap.dedent(inspect.getsource(func))
            def_line = re.search(r'^def\s', source, re.MULTILINE)
            if def_line:
                source = source[def_line.start():]
            source = source.lstrip('\n')
        except (OSError, TypeError):
            source = f"def {func.__name__}(*args, **kwargs):\n    return func(*args, **kwargs)\n"
        entrypoint = manifest.execution.get("entrypoint", "skill.py")
        (tmp / entrypoint).write_text(source)

        try:
            self.forge.installer.install_from_path(tmp)
        except Exception:
            pass

        return func
