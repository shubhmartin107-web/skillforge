from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from skillforge.composition.nodes import (
    BaseNode,
    ConditionNode,
    MapNode,
    MergeNode,
    NodeType,
    SkillNode,
)
from skillforge.models.execution import ExecutionMode, ExecutionRequest, ExecutionStatus
from skillforge.runtime.executor import Executor
from skillforge.runtime.hooks import ExecutionHooks


class WorkflowError(Exception):
    pass


class Workflow:
    def __init__(self, name: str, version: str = "0.1.0", description: str = ""):
        self.name = name
        self.version = version
        self.description = description
        self.nodes: dict[str, BaseNode] = {}
        self.start_node: str | None = None

    def add_node(self, node: BaseNode) -> None:
        self.nodes[node.id] = node
        if self.start_node is None:
            self.start_node = node.id

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "start_node": self.start_node,
            "nodes": {nid: node.model_dump() for nid, node in self.nodes.items()},
        }

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workflow:
        wf = cls(
            name=data.get("name", "unnamed"),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
        )
        wf.start_node = data.get("start_node")
        for nid, node_data in data.get("nodes", {}).items():
            ntype = NodeType(node_data.get("type", "skill"))
            if ntype == NodeType.skill:
                wf.nodes[nid] = SkillNode(**node_data)
            elif ntype == NodeType.condition:
                wf.nodes[nid] = ConditionNode(**node_data)
            elif ntype == NodeType.map_node:
                wf.nodes[nid] = MapNode(**node_data)
            elif ntype == NodeType.merge:
                wf.nodes[nid] = MergeNode(**node_data)
            else:
                raise WorkflowError(f"Unknown node type: {ntype}")
        return wf

    @classmethod
    def from_yaml(cls, path: Path) -> Workflow:
        data = yaml.safe_load(path.read_text("utf-8"))
        return cls.from_dict(data)


class WorkflowEngine:
    def __init__(self, executor: Executor | None = None):
        self.executor = executor or Executor()

    def run(
        self,
        workflow: Workflow,
        inputs: dict[str, Any] | None = None,
        hooks: ExecutionHooks | None = None,
    ) -> dict[str, Any]:
        hooks = hooks or ExecutionHooks()
        context: dict[str, Any] = {"workflow": {"inputs": inputs or {}}}

        if workflow.start_node is None or workflow.start_node not in workflow.nodes:
            raise WorkflowError("Workflow has no valid start node")

        hooks.emit(
            "workflow.started",
            {
                "workflow_name": workflow.name,
                "workflow_version": workflow.version,
            },
        )

        current_id: str | None = workflow.start_node
        visited: set[str] = set()

        while current_id:
            if current_id in visited:
                raise WorkflowError(f"Cycle detected at node '{current_id}'")
            visited.add(current_id)

            node = workflow.nodes.get(current_id)
            if node is None:
                raise WorkflowError(f"Node '{current_id}' not found")

            try:
                if isinstance(node, SkillNode):
                    resolved_inputs = node.resolve_inputs(context)
                    req = ExecutionRequest(
                        skill_name=node.skill_name,
                        skill_version=node.skill_version,
                        inputs=resolved_inputs,
                        mode=ExecutionMode(node.execution_mode),
                        trace_id=hooks.trace_id,
                    )
                    result = self.executor.execute(req, hooks=hooks)

                    context[f"steps.{node.id}.result"] = result.outputs
                    context[f"steps.{node.id}.status"] = result.status.value

                    if result.status == ExecutionStatus.completed:
                        current_id = node.next_on_success
                    else:
                        current_id = node.next_on_failure

                elif isinstance(node, ConditionNode):
                    result_id = node.evaluate(context)
                    context[f"steps.{node.id}.branch"] = result_id
                    current_id = result_id

                elif isinstance(node, MapNode):
                    items = self._resolve_path(context, node.iterate_over)
                    if isinstance(items, list):
                        results = []
                        for _i, item in enumerate(items):
                            item_context = {**context, "item": item}
                            context[f"steps.{node.id}.current"] = item
                            sub_node = workflow.nodes.get(node.node_id)
                            if isinstance(sub_node, SkillNode):
                                resolved = sub_node.resolve_inputs(item_context)
                                req = ExecutionRequest(
                                    skill_name=sub_node.skill_name,
                                    inputs=resolved,
                                    trace_id=hooks.trace_id,
                                )
                                r = self.executor.execute(req, hooks=hooks)
                                results.append(r.outputs)
                        context[f"steps.{node.id}.results"] = results
                    current_id = node.next_on_success

                elif isinstance(node, MergeNode):
                    merged: dict[str, Any] = {}
                    for inp_id in node.input_nodes:
                        key = f"steps.{inp_id}.result"
                        if key in context:
                            val = context[key]
                            if isinstance(val, dict):
                                merged.update(val)
                            else:
                                merged[inp_id] = val
                    context[f"steps.{node.id}.result"] = merged
                    current_id = node.next_on_success

                else:
                    current_id = None

            except Exception as e:
                hooks.emit(
                    "workflow.failed",
                    {
                        "node_id": current_id,
                        "error": str(e),
                    },
                )
                raise WorkflowError(f"Workflow failed at node '{current_id}': {e}")

        hooks.emit("workflow.completed", {"status": "completed"})
        return context

    def _resolve_path(self, context: dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        current: Any = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, {})
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current
