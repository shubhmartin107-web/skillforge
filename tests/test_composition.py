from __future__ import annotations

from pathlib import Path

from skillforge.composition.nodes import ConditionNode, SkillNode
from skillforge.composition.workflow import Workflow, WorkflowEngine
from skillforge.runtime.executor import Executor


class TestWorkflow:
    def test_single_skill_workflow(self, installer, registry):
        skill_dir = Path("/tmp/sf_test_wf_skill")
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "skill.yaml").write_text("""
name: wf-adder
version: 1.0.0
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

        wf = Workflow(name="test-wf")
        wf.add_node(
            SkillNode(
                id="step1",
                skill_name="wf-adder",
                inputs={"a": "{workflow.inputs.x}", "b": "{workflow.inputs.y}"},
            )
        )

        executor = Executor(registry=registry)
        engine = WorkflowEngine(executor=executor)
        context = engine.run(wf, inputs={"x": 5, "y": 3})

        assert "steps.step1.result" in context
        assert context["steps.step1.result"]["sum"] == 8

    def test_conditional_workflow(self):
        wf = Workflow(name="cond-wf")
        wf.add_node(
            ConditionNode(
                id="check",
                condition="{steps.previous.value} > 10",
                true_branch="large",
                false_branch="small",
            )
        )

        result_id = wf.nodes["check"].evaluate({"steps.previous.value": 15})
        assert result_id == "large"

        result_id = wf.nodes["check"].evaluate({"steps.previous.value": 5})
        assert result_id == "small"

    def test_workflow_serialization(self):
        wf = Workflow(name="serial-test", version="1.0.0")
        wf.add_node(SkillNode(id="s1", skill_name="test"))
        wf.add_node(ConditionNode(id="c1", condition="true", true_branch="s1", false_branch="s1"))

        data = wf.to_dict()
        restored = Workflow.from_dict(data)

        assert restored.name == "serial-test"
        assert restored.version == "1.0.0"
        assert len(restored.nodes) == 2
        assert "s1" in restored.nodes
        assert "c1" in restored.nodes
