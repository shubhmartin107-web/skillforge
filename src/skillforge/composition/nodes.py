from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    skill = "skill"
    condition = "condition"
    map_node = "map"
    merge = "merge"


class BaseNode(BaseModel):
    id: str
    type: NodeType
    description: str = ""
    next_on_success: str | None = None
    next_on_failure: str | None = None


class SkillNode(BaseNode):
    type: NodeType = NodeType.skill
    skill_name: str
    skill_version: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict)
    execution_mode: str = "direct"

    def resolve_inputs(self, context: dict[str, Any]) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for key, value in self.inputs.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                path = value[1:-1].split(".")
                resolved[key] = self._resolve_path(context, path)
            else:
                resolved[key] = value
        return resolved

    def _resolve_path(self, context: dict[str, Any], path: list[str]) -> Any:
        current: Any = context
        for part in path:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current


class ConditionNode(BaseNode):
    type: NodeType = NodeType.condition
    condition: str
    true_branch: str
    false_branch: str

    def evaluate(self, context: dict[str, Any]) -> str:

        expr = self.condition
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if isinstance(value, str):
                expr = expr.replace(placeholder, f'"{value}"')
            else:
                expr = expr.replace(placeholder, str(value))

        try:
            result = eval(expr, {"__builtins__": {}}, {})
            return self.true_branch if result else self.false_branch
        except Exception:
            return self.false_branch


class MapNode(BaseNode):
    type: NodeType = NodeType.map_node
    iterate_over: str
    node_id: str


class MergeNode(BaseNode):
    type: NodeType = NodeType.merge
    input_nodes: list[str] = Field(default_factory=list)
    merge_strategy: str = "dict"  # dict | list | concat
