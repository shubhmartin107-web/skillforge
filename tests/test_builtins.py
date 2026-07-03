from __future__ import annotations

import importlib.util
from pathlib import Path

from skillforge.models.execution import ExecutionRequest
from skillforge.runtime.executor import Executor


class TestBuiltinEcho:
    def test_echo_basic(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent / "src" / "skillforge" / "skills" / "builtins" / "echo"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(ExecutionRequest(skill_name="echo", inputs={"message": "test"}))
        assert result.success
        assert result.outputs["result"] == "test"

    def test_echo_uppercase(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent / "src" / "skillforge" / "skills" / "builtins" / "echo"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(
            ExecutionRequest(skill_name="echo", inputs={"message": "hello", "uppercase": True})
        )
        assert result.success
        assert result.outputs["result"] == "HELLO"


class TestBuiltinCalculator:
    def test_add(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent
            / "src"
            / "skillforge"
            / "skills"
            / "builtins"
            / "calculator"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(
            ExecutionRequest(skill_name="calculator", inputs={"a": 5, "b": 3, "operation": "add"})
        )
        assert result.success
        assert result.outputs["result"] == 8

    def test_mul(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent
            / "src"
            / "skillforge"
            / "skills"
            / "builtins"
            / "calculator"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(
            ExecutionRequest(skill_name="calculator", inputs={"a": 4, "b": 5, "operation": "mul"})
        )
        assert result.success
        assert result.outputs["result"] == 20

    def test_divide_by_zero(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent
            / "src"
            / "skillforge"
            / "skills"
            / "builtins"
            / "calculator"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(
            ExecutionRequest(skill_name="calculator", inputs={"a": 1, "b": 0, "operation": "div"})
        )
        assert result.success
        assert result.outputs["result"] == float("inf")


class TestBuiltinTemplate:
    def test_basic_template(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent
            / "src"
            / "skillforge"
            / "skills"
            / "builtins"
            / "template-renderer"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(
            ExecutionRequest(
                skill_name="template-renderer",
                inputs={"template": "Hello {name}!", "variables": {"name": "World"}},
            )
        )
        assert result.success
        assert result.outputs["result"] == "Hello World!"
        assert result.outputs["placeholders_replaced"] == 1


class TestBuiltinFileReader:
    def test_file_not_found(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent
            / "src"
            / "skillforge"
            / "skills"
            / "builtins"
            / "file-reader"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(
            ExecutionRequest(
                skill_name="file-reader", inputs={"path": "/tmp/nonexistent_file_xyz.txt"}
            )
        )
        assert result.success
        assert "error" in result.outputs or result.outputs.get("content") == ""


class TestBuiltinJSON:
    def test_valid_json(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent
            / "src"
            / "skillforge"
            / "skills"
            / "builtins"
            / "json-processor"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(
            ExecutionRequest(
                skill_name="json-processor",
                inputs={"data": '{"name": "test"}', "pretty_print": True},
            )
        )
        assert result.success
        assert result.outputs["valid"] is True

    def test_invalid_json(self, installer, registry):
        skill_dir = (
            Path(__file__).parent.parent
            / "src"
            / "skillforge"
            / "skills"
            / "builtins"
            / "json-processor"
        )
        installer.install_from_path(skill_dir)
        executor = Executor(registry=registry)

        result = executor.execute(
            ExecutionRequest(skill_name="json-processor", inputs={"data": "not json"})
        )
        assert result.success
        assert result.outputs["valid"] is False


class TestBuiltinXquikResearch:
    def test_success_result_shape(self, monkeypatch):
        skill_path = (
            Path(__file__).parent.parent
            / "src"
            / "skillforge"
            / "skills"
            / "builtins"
            / "xquik-research"
            / "skill.py"
        )
        spec = importlib.util.spec_from_file_location("xquik_research_skill", skill_path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FakeResponse:
            status_code = 200
            text = '{"ok": true}'

            def json(self):
                return {"ok": True}

        class FakeClient:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def get(self, url, params, headers):
                assert url == "https://xquik.com/api/v1/x/tweets/search"
                assert params == {"q": "xquik"}
                assert headers["X-API-Key"] == "test-key"
                return FakeResponse()

        monkeypatch.setattr(module.httpx, "Client", FakeClient)

        result = module.query_xquik(
            endpoint="/api/v1/x/tweets/search",
            api_key="test-key",
            query={"q": "xquik"},
        )

        assert result["status_code"] == 200
        assert result["data"] == {"ok": True}
        assert result["body"] == ""
        assert isinstance(result["elapsed_ms"], int)
