from __future__ import annotations

import importlib.util
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
from skillforge.runtime.sandbox import Sandbox


class WasmSandboxError(Exception):
    pass


class WasmSandbox:
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
        self.network_enabled = (
            network_enabled if network_enabled is not None else settings.network_enabled
        )
        self._tmpdir: Path | None = None
        self._wasm_backend: str | None = None
        self._wasm_available = self._check_wasm_support()

    def _check_wasm_support(self) -> bool:
        if importlib.util.find_spec("wasmtime") is not None:
            self._wasm_backend = "wasmtime"
            return True
        if importlib.util.find_spec("wasmer") is not None:
            self._wasm_backend = "wasmer"
            return True
        self._wasm_backend = None
        return False

    @property
    def workdir(self) -> Path:
        if self._tmpdir is None:
            raise WasmSandboxError("Sandbox not active. Use as context manager.")
        return self._tmpdir

    def __enter__(self) -> WasmSandbox:
        self._tmpdir = Path(tempfile.mkdtemp(prefix="skillforge_wasm_"))
        return self

    def __exit__(self, *args: Any) -> None:
        if self._tmpdir and self._tmpdir.exists():
            shutil.rmtree(self._tmpdir, ignore_errors=True)
        self._tmpdir = None

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
        if self._wasm_available:
            return self._execute_wasm(code, function_name, inputs or {})
        return self._execute_fallback(code, function_name, inputs or {})

    def _execute_wasm(
        self,
        code: str,
        function_name: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        import json as _json

        wrapper = (
            "import json, sys, os\n"
            "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
            "\n"
            f"{code}\n"
            "\n"
            f"_inputs = {_json.dumps(inputs)}\n"
            f"_result = {function_name}(**_inputs)\n"
            'print("__SKILLFORGE_RESULT__" + json.dumps(_result))\n'
        )

        script_path = self.workdir / "_wasm_runner.py"
        script_path.write_text(wrapper)

        if self._wasm_backend == "wasmtime":
            return self._run_wasmtime(script_path)
        return self._run_wasmer(script_path)

    def _run_wasmtime(self, script_path: Path) -> dict[str, Any]:
        import wasmtime

        wasm_bytes = self._compile_python_to_wasm(script_path)
        if wasm_bytes is None:
            return self._execute_fallback(script_path.read_text("utf-8"), "run", {})

        engine = wasmtime.Engine(
            config=wasmtime.Config() if not hasattr(wasmtime, "Config") else wasmtime.Config()
        )
        try:
            module = wasmtime.Module(engine, wasm_bytes)
            linker = wasmtime.Linker(engine)
            store = wasmtime.Store(engine)

            memory_limit = self.max_memory_mb * 1024 * 1024
            linker.define(store, "env", "memory", wasmtime.Memory(store, memory_limit))

            instance = linker.instantiate(store, module)
            result = instance.exports(store).get("run")
            if result:
                output = result(store)
                return {"result": str(output)}

            return self._execute_fallback(script_path.read_text("utf-8"), "run", {})
        except Exception as e:
            return self._execute_fallback(
                script_path.read_text("utf-8"),
                "run",
                {},
                f"Wasmtime error, falling back: {e}",
            )

    def _run_wasmer(self, script_path: Path) -> dict[str, Any]:
        import wasmer

        wasm_bytes = self._compile_python_to_wasm(script_path)
        if wasm_bytes is None:
            return self._execute_fallback(script_path.read_text("utf-8"), "run", {})

        try:
            store = wasmer.Store()
            module = wasmer.Module(store, wasm_bytes)
            import wasmer_compiler_cranelift

            compiler = wasmer_compiler_cranelift.Compiler()
            instance = wasmer.Instance(module, compiler=compiler)

            run_func = instance.exports.run
            if run_func:
                result = run_func()
                return {"result": str(result)}

            return self._execute_fallback(script_path.read_text("utf-8"), "run", {})
        except Exception as e:
            return self._execute_fallback(
                script_path.read_text("utf-8"),
                "run",
                {},
                f"Wasmer error, falling back: {e}",
            )

    def _compile_python_to_wasm(self, script_path: Path) -> bytes | None:
        try:
            import pyodide

            source = script_path.read_text("utf-8")
            wasm_module = pyodide.compile(source)
            return wasm_module
        except ImportError:
            pass
        try:
            import micropython

            source = script_path.read_text("utf-8")
            return micropython.compile_to_wasm(source)
        except (ImportError, AttributeError):
            pass
        return None

    def _execute_fallback(
        self,
        code: str,
        function_name: str,
        inputs: dict[str, Any],
        error_context: str = "",
    ) -> dict[str, Any]:
        import json as _json

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
            for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
                env.pop(var, None)
        for var_name in self.permissions.env_vars:
            if var_name in os.environ:
                env[var_name] = os.environ[var_name]

        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env.pop("LD_PRELOAD", None)
        env.pop("LD_LIBRARY_PATH", None)

        input_json = _json.dumps(inputs)

        try:
            proc = subprocess.run(
                [sys.executable, str(script_path), input_json],
                cwd=str(self.workdir),
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                preexec_fn=self._restrict_resources_enhanced,
            )
        except subprocess.TimeoutExpired:
            msg = f"{error_context}Execution timed out after {self.timeout}s".strip()
            raise WasmSandboxError(msg) from None
        except FileNotFoundError:
            raise WasmSandboxError("Python interpreter not found") from None

        if proc.returncode != 0:
            raise WasmSandboxError(
                f"Skill execution failed (exit code {proc.returncode}): {proc.stderr.strip()}"
            )

        marker = "__SKILLFORGE_RESULT__"
        if marker in proc.stdout:
            result_json = proc.stdout.split(marker, 1)[1].strip()
            try:
                return _json.loads(result_json)
            except Exception as e:
                raise WasmSandboxError(f"Failed to parse result: {e}") from None
        else:
            return {"stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}

    def _restrict_resources_enhanced(self) -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout + 5))
        mem_bytes = self.max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
        resource.setrlimit(resource.RLIMIT_NPROC, (16, 16))
        signal.signal(
            signal.SIGALRM,
            lambda *_: (_ for _ in ()).throw(TimeoutError("Execution timed out")),
        )
        signal.alarm(self.timeout)

        os.nice(5)

        try:
            import ctypes

            libc = ctypes.CDLL("libc.so.6", use_errno=True)

            pr_set_no_new_privs = 38
            libc.prctl(pr_set_no_new_privs, 1, 0, 0, 0)

            from contextlib import suppress

            with suppress(Exception):
                libc.unshare(0x10000000)
        except Exception:
            pass

        for sig in (signal.SIGPIPE, signal.SIGTTIN, signal.SIGTTOU):
            signal.signal(sig, signal.SIG_DFL)


def create_sandbox(use_wasm: bool = True) -> WasmSandbox | Sandbox:
    if use_wasm:
        return WasmSandbox()
    return Sandbox()
