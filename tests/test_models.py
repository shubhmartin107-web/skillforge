from __future__ import annotations

from skillforge.models.skill import SkillInput, SkillManifest
from skillforge.models.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from skillforge.models.registry import RegistryEntry, SearchQuery


class TestSkillManifest:
    def test_minimal_manifest(self):
        m = SkillManifest(name="test", version="1.0.0")
        assert m.name == "test"
        assert m.version == "1.0.0"
        assert m.execution["mode"] == "direct"

    def test_invalid_semver(self):
        import pytest
        with pytest.raises(Exception):
            SkillManifest(name="test", version="not-a-version")

    def test_invalid_name(self):
        import pytest
        with pytest.raises(Exception):
            SkillManifest(name="", version="1.0.0")
        with pytest.raises(Exception):
            SkillManifest(name="-bad-start", version="1.0.0")

    def test_manifest_with_inputs(self):
        m = SkillManifest(
            name="greeter",
            version="0.1.0",
            inputs=[
                SkillInput(name="name", type="string", required=True),
                SkillInput(name="greeting", type="string", default="Hello"),
            ],
        )
        assert len(m.inputs) == 2
        assert m.inputs[0].name == "name"
        assert m.inputs[1].default == "Hello"


class TestExecution:
    def test_execution_request(self):
        req = ExecutionRequest(skill_name="test", inputs={"key": "value"})
        assert req.skill_name == "test"
        assert req.inputs["key"] == "value"
        assert req.mode.value == "direct"

    def test_execution_result_success(self):
        result = ExecutionResult(
            request=ExecutionRequest(skill_name="test"),
            status=ExecutionStatus.completed,
            outputs={"result": 42},
        )
        assert result.success
        assert result.outputs["result"] == 42

    def test_execution_result_failure(self):
        result = ExecutionResult(
            request=ExecutionRequest(skill_name="test"),
            status=ExecutionStatus.failed,
            error="Something went wrong",
        )
        assert not result.success
        assert "Something went wrong" in result.error


class TestRegistry:
    def test_registry_entry(self):
        entry = RegistryEntry(name="test", version="1.0.0")
        assert entry.name == "test"
        assert entry.version == "1.0.0"

    def test_search_query(self):
        q = SearchQuery(query="test", tags=["utility"], limit=10)
        assert q.query == "test"
        assert "utility" in q.tags
        assert q.limit == 10
