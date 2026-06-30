from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from skillforge.config import settings
from skillforge.models.execution import (
    ExecutionMode,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from skillforge.models.skill import SkillManifest
from skillforge.registry.local import LocalRegistry
from skillforge.runtime.hooks import ExecutionHooks
from skillforge.runtime.sandbox import Sandbox
from skillforge.runtime.wasm_sandbox import WasmSandbox


class Executor:
    def __init__(self, registry: LocalRegistry | None = None):
        self.registry = registry or LocalRegistry()

    def execute(
        self,
        request: ExecutionRequest,
        hooks: ExecutionHooks | None = None,
    ) -> ExecutionResult:
        hooks = hooks or ExecutionHooks(trace_id=request.trace_id)
        result = ExecutionResult(
            request=request,
            trace_id=hooks.trace_id,
            started_at=datetime.now(),
        )

        try:
            entry = self.registry.get(request.skill_name, request.skill_version)
            if entry is None:
                raise ValueError(f"Skill '{request.skill_name}' not found in registry")

            skill_dir = Path(entry.skill_path)
            if not skill_dir.exists():
                raise ValueError(f"Skill directory not found: {skill_dir}")

            manifest_path = Path(entry.manifest_path)
            if manifest_path.exists():
                import yaml
                raw = yaml.safe_load(manifest_path.read_text("utf-8"))
                manifest = SkillManifest.from_yaml_dict(raw)
            else:
                manifest = None

            hooks.start(skill_name=request.skill_name, mode=request.mode.value)

            if request.mode == ExecutionMode.direct:
                outputs = self._execute_direct(skill_dir, entry, request, manifest)
            elif request.mode == ExecutionMode.tool_calling:
                outputs = self._execute_tool_calling(skill_dir, entry, request, manifest)
            else:
                raise ValueError(f"Unsupported execution mode: {request.mode}")

            result.outputs = outputs
            result.status = ExecutionStatus.completed
            hooks.complete(outputs=outputs)
            hooks.output(outputs)

        except Exception as e:
            result.status = ExecutionStatus.failed
            result.error = str(e)
            hooks.fail(error=str(e))

        result.completed_at = datetime.now()
        result.duration_ms = result.runtime_ms
        result.events = hooks.get_events()
        return result

    def _execute_direct(
        self,
        skill_dir: Path,
        entry: Any,
        request: ExecutionRequest,
        manifest: SkillManifest | None,
    ) -> dict[str, Any]:
        entrypoint = entry.entrypoint or "skill.py"
        entry_path = skill_dir / entrypoint

        if not entry_path.exists():
            raise FileNotFoundError(f"Entrypoint not found: {entry_path}")

        spec = importlib.util.spec_from_file_location(f"skill_{entry.name}", entry_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load skill module: {entry_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[f"skill_{entry.name}"] = module
        spec.loader.exec_module(module)

        func_name = manifest.execution.get("function", "run") if manifest else "run"
        if not hasattr(module, func_name):
            raise AttributeError(f"Function '{func_name}' not found in {entrypoint}")

        func = getattr(module, func_name)

        try:
            result = func(**request.inputs)
        except TypeError as e:
            raise TypeError(f"Function signature mismatch for '{func_name}': {e}")

        if result is None:
            return {}
        if isinstance(result, dict):
            return result
        return {"result": result}

    def _execute_tool_calling(
        self,
        skill_dir: Path,
        entry: Any,
        request: ExecutionRequest,
        manifest: SkillManifest | None,
    ) -> dict[str, Any]:
        if manifest is None:
            raise ValueError("Manifest required for tool-calling mode")

        tool_def = self._build_tool_definition(manifest)
        outputs = self._execute_direct(skill_dir, entry, request, manifest)
        return {"tool_definition": tool_def, "outputs": outputs}

    def _build_tool_definition(self, manifest: SkillManifest) -> dict[str, Any]:
        properties = {}
        required = []
        for inp in manifest.inputs:
            prop = {"type": inp.type, "description": inp.description}
            if inp.default is not None:
                pass
            properties[inp.name] = prop
            if inp.required:
                required.append(inp.name)

        return {
            "type": "function",
            "function": {
                "name": manifest.name,
                "description": manifest.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required if required else None,
                },
            },
        }

    def execute_in_sandbox(
        self,
        request: ExecutionRequest,
        hooks: ExecutionHooks | None = None,
    ) -> ExecutionResult:
        hooks = hooks or ExecutionHooks(trace_id=request.trace_id)
        result = ExecutionResult(
            request=request,
            trace_id=hooks.trace_id,
            started_at=datetime.now(),
        )

        try:
            entry = self.registry.get(request.skill_name, request.skill_version)
            if entry is None:
                raise ValueError(f"Skill '{request.skill_name}' not found in registry")

            skill_dir = Path(entry.skill_path)
            if not skill_dir.exists():
                raise ValueError(f"Skill directory not found: {skill_dir}")

            import yaml
            manifest_path = Path(entry.manifest_path)
            raw = yaml.safe_load(manifest_path.read_text("utf-8")) if manifest_path.exists() else {}
            manifest = SkillManifest.from_yaml_dict(raw) if raw else SkillManifest(name=entry.name, version=entry.version)
            permissions = manifest.permissions

            hooks.start(skill_name=request.skill_name, mode="sandboxed")

            use_wasm = settings.sandbox_mode in ("auto", "wasm")
            sandbox_cls: type[Sandbox | WasmSandbox] = WasmSandbox if use_wasm else Sandbox
            with sandbox_cls(
                permissions=permissions,
                timeout=request.timeout or settings.execution_timeout,
                network_enabled=permissions.network,
            ) as sandbox:
                sandbox.prepare_skill(skill_dir)

                entrypoint = entry.entrypoint or "skill.py"
                entry_path = sandbox.workdir / "skill" / entrypoint
                if not entry_path.exists():
                    raise FileNotFoundError(f"Entrypoint not found in sandbox: {entry_path}")

                code = entry_path.read_text("utf-8")
                func_name = manifest.execution.get("function", "run") if manifest else "run"
                outputs = sandbox.execute_python(code, function_name=func_name, inputs=request.inputs)

            result.outputs = outputs
            result.status = ExecutionStatus.completed
            hooks.complete(outputs=outputs)
            hooks.output(outputs)

        except Exception as e:
            result.status = ExecutionStatus.failed
            result.error = str(e)
            hooks.fail(error=str(e))

        result.completed_at = datetime.now()
        result.duration_ms = result.runtime_ms
        result.events = hooks.get_events()
        return result
