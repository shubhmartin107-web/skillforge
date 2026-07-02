from __future__ import annotations

import inspect
import re
import tempfile
import textwrap
from collections.abc import Callable
from pathlib import Path

from skillforge.models.skill import SkillInput, SkillManifest
from skillforge.registry.installer import Installer
from skillforge.registry.local import LocalRegistry


def skill(
    name: str,
    version: str = "0.1.0",
    description: str = "",
    inputs: list[SkillInput] | None = None,
    network: bool = False,
    tags: list[str] | None = None,
    categories: list[str] | None = None,
    auto_register: bool = True,
):
    def decorator(func: Callable) -> Callable:
        manifest = SkillManifest(
            name=name,
            version=version,
            description=description or func.__doc__ or "",
            inputs=inputs or [],
            outputs=[],
            permissions={
                "network": network,
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
            tags=tags or [],
            categories=categories or [],
        )

        if auto_register:
            tmp = Path(tempfile.mkdtemp(prefix="skillforge_decorator_"))
            import yaml

            (tmp / "skill.yaml").write_text(
                yaml.dump(manifest.to_yaml_dict(), default_flow_style=False)
            )

            try:
                source = textwrap.dedent(inspect.getsource(func))
                def_line = re.search(r"^def\s", source, re.MULTILINE)
                if def_line:
                    source = source[def_line.start() :]
                source = source.lstrip("\n")
            except (OSError, TypeError):
                source = (
                    f"def {func.__name__}(*args, **kwargs):\n    return func(*args, **kwargs)\n"
                )

            entrypoint = manifest.execution.get("entrypoint", "skill.py")
            (tmp / entrypoint).write_text(source)

            try:
                registry = LocalRegistry()
                installer = Installer(registry=registry)
                installer.install_from_path(tmp)
            except Exception:
                pass

        return func

    return decorator
