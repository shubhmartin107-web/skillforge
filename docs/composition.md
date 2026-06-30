# Composition & Workflows

SkillForge allows composing multiple skills into higher-level workflows using a DAG-based engine.

## Workflow Format

Workflows are defined in YAML:

```yaml
name: my-workflow
version: 0.1.0
start_node: step1

nodes:
  step1:
    type: skill
    skill_name: my-skill
    inputs:
      param1: "{workflow.inputs.value}"
    next_on_success: step2
    next_on_failure: error_handler

  step2:
    type: skill
    skill_name: another-skill
    inputs:
      data: "{steps.step1.result.output_value}"
```

## Node Types

| Type | Description |
|------|-------------|
| `skill` | Execute a skill with resolved inputs |
| `condition` | Evaluate an expression, branch to true/false node |
| `map` | Iterate over a list, execute a sub-node for each item |
| `merge` | Combine outputs from multiple nodes |

## Input Resolution

Inputs can reference workflow or step outputs using template syntax:

- `{workflow.inputs.key}` — Top-level workflow input
- `{steps.node_id.result.field}` — Output from a previous step
- `{item}` — Current item in a map iteration

## Running Workflows

```bash
# Validate
skillforge workflow validate my-workflow.yaml

# Run with inputs
skillforge workflow run my-workflow.yaml -i value="test"
```

## SDK Usage

```python
from skillforge.composition.workflow import Workflow, WorkflowEngine
from skillforge.composition.nodes import SkillNode
from skillforge.runtime.executor import Executor

wf = Workflow(name="my-workflow")
wf.add_node(SkillNode(
    id="step1",
    skill_name="my-skill",
    inputs={"key": "{workflow.inputs.value}"},
))

engine = WorkflowEngine(executor=Executor())
context = engine.run(wf, inputs={"value": "test"})
```
