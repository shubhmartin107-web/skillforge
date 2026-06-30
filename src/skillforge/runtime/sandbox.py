from __future__ import annotations

import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from skillforge.config import settings
from skillforge.models.skill import Permission


class SandboxError(Exception):
    pass


class Sandbox:
    def __init__(
        self,
        permissions: Permission | None = None,
        timeout: int | None = None,
        max_memory_mb: int | None = None,
        network_enabled: bool | None = None,
    ):
        self.permissions = permissions or Permission()
        self.timeout = timeout or settings.execution_timeout
        self.max_memory_mb = max_memory_mb or settings.max_memory_mb
        self.network_enabled = network_enabled if network_enabled is not None else settings.network_enabled
        self._tmpdir: Path | None = None

    def __enter__(self) -> Sandbox:
        self._tmpdir = Path(tempfile.mkdtemp(prefix="skillforge_"))
        return self

    def __exit__(self, *args: Any) -> None:
        if self._tmpdir and self._tmpdir.exists():
            shutil.rmtree(self._tmpdir, ignore_errors=True)
        self._tmpdir = None

    @property
    def workdir(self) -> Path:
        if self._tmpdir is None:
            raise SandboxError("Sandbox not active. Use as context manager.")
        return self._tmpdir

    def prepare_skill(self, skill_path: Path) -> Path:
        dest = self.workdir / "skill"
        if skill_path.exists():
            if skill_path.is_dir():
                shutil.copytree(skill_path, dest, dirs_exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(skill_path, dest)
        return dest

    def execute_python(
        self,
        code: str,
        function_name: str = "run",
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        inputs = inputs or {}

        wrapper = (
            "import json, sys, os\n"
            "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
            "\n"
            f"{code}\n"
            "\n"
            f"_inputs = json.loads(sys.argv[1])\n"
            f"_result = {function_name}(**_inputs)\n"
            'print("__SKILLFORGE_RESULT__" + json.dumps(_result))\n'
        )

        script_path = self.workdir / "_runner.py"
        script_path.write_text(wrapper)

        env = os.environ.copy()
        if not self.network_enabled:
            env.pop("HTTP_PROXY", None)
            env.pop("HTTPS_PROXY", None)
            env.pop("http_proxy", None)
            env.pop("https_proxy", None)

        for var_name in self.permissions.env_vars:
            if var_name in os.environ:
                env[var_name] = os.environ[var_name]

        import json as _json
        input_json = _json.dumps(inputs)

        try:
            proc = subprocess.run(
                [sys.executable, str(script_path), input_json],
                cwd=str(self.workdir),
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                preexec_fn=self._restrict_resources,
            )
        except subprocess.TimeoutExpired:
            raise SandboxError(f"Execution timed out after {self.timeout}s")
        except FileNotFoundError:
            raise SandboxError("Python interpreter not found")

        if proc.returncode != 0:
            raise SandboxError(
                f"Skill execution failed (exit code {proc.returncode}): {proc.stderr.strip()}"
            )

        marker = "__SKILLFORGE_RESULT__"
        if marker in proc.stdout:
            result_json = proc.stdout.split(marker, 1)[1].strip()
            try:
                import json as _json2
                return _json2.loads(result_json)
            except Exception as e:
                raise SandboxError(f"Failed to parse result: {e}")
        else:
            return {"stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}

    def _restrict_resources(self) -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout + 5))
        mem_bytes = self.max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("Execution timed out")))
        signal.alarm(self.timeout)
