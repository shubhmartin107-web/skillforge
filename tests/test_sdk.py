from __future__ import annotations

import os
import uuid
from pathlib import Path

from skillforge import Forge
from skillforge.models.skill import SkillInput


def _unique_name(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class TestForge:
    def test_create_skill(self):
        name = _unique_name("create")
        with Forge() as forge:
            skill_dir = forge.create_skill(name, path=f"/tmp/{name}")
            assert skill_dir.exists()
            assert (skill_dir / "skill.yaml").exists()
            assert (skill_dir / "skill.py").exists()

    def test_install_and_run(self):
        name = _unique_name("run")
        with Forge() as forge:
            skill_dir = Path(f"/tmp/{name}")
            skill_dir.mkdir(exist_ok=True)
            (skill_dir / "skill.yaml").write_text(f"""
name: {name}
version: 1.0.0
inputs:
  - name: x
    type: integer
outputs:
  - name: result
    type: integer
execution:
  mode: direct
  entrypoint: skill.py
  function: run
""")
            (skill_dir / "skill.py").write_text("def run(x): return {'result': x * 2}")

            forge.install(str(skill_dir))
            result = forge.run(name, x=21)
            assert result.success
            assert result.outputs["result"] == 42

    def test_search(self):
        with Forge() as forge:
            result = forge.search()
            assert result is not None

    def test_stats(self):
        with Forge() as forge:
            stats = forge.stats()
            assert stats is not None

    def test_validate_manifest(self):
        name = _unique_name("validate")
        with Forge() as forge:
            skill_dir = Path(f"/tmp/{name}")
            skill_dir.mkdir(exist_ok=True)
            manifest_path = skill_dir / "skill.yaml"
            manifest_path.write_text(f"name: {name}\nversion: 1.0.0\n")
            manifest = forge.validate_manifest(str(manifest_path))
            assert manifest.name == name
            assert manifest.version == "1.0.0"

    def test_register_skill_inline(self):
        name = _unique_name("inline")
        with Forge() as forge:
            @forge.register_skill(
                name=name,
                description="An inline test skill",
                inputs=[SkillInput(name="msg", type="string")],
            )
            def my_skill(msg: str) -> dict:
                return {"echo": msg}

            result = forge.run(name, msg="hello")
            assert result.success, f"Failed: {result.error}"
            assert result.outputs["echo"] == "hello"

    def test_async_run(self):
        import asyncio

        name = _unique_name("async")

        async def test():
            with Forge() as forge:
                skill_dir = Path(f"/tmp/{name}")
                skill_dir.mkdir(exist_ok=True)
                (skill_dir / "skill.yaml").write_text(f"""
name: {name}
version: 1.0.0
inputs:
  - name: v
    type: integer
execution:
  mode: direct
  entrypoint: skill.py
  function: run
""")
                (skill_dir / "skill.py").write_text("def run(v): return {'result': v * 2}")

                forge.install(str(skill_dir))
                result = await forge.run_async(name, v=10)
                assert result.success, f"Async failed: {result.error}"
                assert result.outputs["result"] == 20

        asyncio.run(test())

    def test_context_manager(self):
        with Forge() as forge:
            assert forge.registry is not None
        forge.close()
