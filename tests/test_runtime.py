from __future__ import annotations

from pathlib import Path

from skillforge.models.execution import ExecutionRequest
from skillforge.runtime.executor import Executor


class TestExecutor:
    def test_direct_execution(self, installer, registry):
        skill_dir = Path("/tmp/sf_test_direct")
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "skill.yaml").write_text("""
name: doubler
version: 1.0.0
description: Doubles a number
inputs:
  - name: x
    type: integer
outputs:
  - name: result
    type: integer
execution:
  mode: direct
  entrypoint: skill.py
  function: double
""")
        (skill_dir / "skill.py").write_text("def double(x): return {'result': x * 2}")

        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        req = ExecutionRequest(skill_name="doubler", inputs={"x": 21})
        result = executor.execute(req)

        assert result.success
        assert result.outputs["result"] == 42

    def test_sandbox_execution(self, installer, registry):
        skill_dir = Path("/tmp/sf_test_sandbox")
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "skill.yaml").write_text("""
name: add
version: 1.0.0
description: Adds two numbers
inputs:
  - name: a
    type: integer
  - name: b
    type: integer
outputs:
  - name: sum
    type: integer
execution:
  mode: direct
  entrypoint: skill.py
  function: add
""")
        (skill_dir / "skill.py").write_text("def add(a, b): return {'sum': a + b}")

        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        req = ExecutionRequest(skill_name="add", inputs={"a": 10, "b": 20})
        result = executor.execute_in_sandbox(req)

        assert result.success
        assert result.outputs["sum"] == 30

    def test_missing_skill(self, registry):
        executor = Executor(registry=registry)
        req = ExecutionRequest(skill_name="nonexistent")
        result = executor.execute(req)
        assert not result.success
        assert "not found" in (result.error or "")

    def test_hooks_integration(self, installer, registry):
        from skillforge.runtime.hooks import ExecutionHooks

        skill_dir = Path("/tmp/sf_test_hooks")
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "skill.yaml").write_text("""
name: echo
version: 1.0.0
description: Echo
inputs:
  - name: msg
    type: string
execution:
  mode: direct
  entrypoint: skill.py
  function: echo
""")
        (skill_dir / "skill.py").write_text("def echo(msg): return {'echo': msg}")

        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        hooks = ExecutionHooks()
        events = []

        def on_event(payload):
            events.append(payload["event"])

        hooks.on("skill.started", on_event)
        hooks.on("skill.completed", on_event)

        req = ExecutionRequest(skill_name="echo", inputs={"msg": "test"}, trace_id=hooks.trace_id)
        result = executor.execute(req, hooks=hooks)

        assert result.success
        assert "skill.started" in events
        assert "skill.completed" in events
