from __future__ import annotations

from pathlib import Path
from typing import Any

BUILTINS_DIR = Path(__file__).parent


def get_builtin_skills() -> list[dict[str, Any]]:
    skills = []
    for entry in BUILTINS_DIR.iterdir():
        if entry.is_dir():
            manifest_path = entry / "skill.yaml"
            if manifest_path.exists():
                import yaml
                manifest = yaml.safe_load(manifest_path.read_text("utf-8"))
                skills.append(manifest)
    return skills


def install_builtins(registry: Any) -> list[Any]:
    from skillforge.registry.installer import Installer
    installer = Installer(registry=registry)
    entries = []
    for entry in BUILTINS_DIR.iterdir():
        if entry.is_dir() and (entry / "skill.yaml").exists():
            try:
                entry_obj = installer.install_from_path(entry)
                entries.append(entry_obj)
            except Exception:
                pass
    return entries
