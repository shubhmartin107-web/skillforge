from __future__ import annotations

import json
from pathlib import Path

from skillforge.composition.workflow import Workflow, WorkflowEngine
from skillforge.runtime.executor import Executor


def create_workflows_page():
    import gradio as gr

    def run_workflow_from_yaml(yaml_content: str, inputs_json: str) -> tuple[str, str]:
        if not yaml_content.strip():
            return "Please enter a workflow YAML definition.", ""

        import yaml
        try:
            data = yaml.safe_load(yaml_content)
            workflow = Workflow.from_dict(data)
        except Exception as e:
            return f"Invalid workflow YAML: {e}", ""

        try:
            inputs = json.loads(inputs_json) if inputs_json.strip() else {}
        except json.JSONDecodeError as e:
            return f"Invalid JSON inputs: {e}", ""

        try:
            engine = WorkflowEngine()
            context = engine.run(workflow, inputs=inputs)
            result = {}
            for key, value in context.items():
                if key.startswith("steps."):
                    result[key] = value
            return json.dumps(result, indent=2, default=str), "Workflow completed successfully!"
        except Exception as e:
            return "", f"Workflow failed: {e}"

    def load_example_workflow() -> str:
        return """name: greeting-workflow
version: 0.1.0
description: "Example workflow"
start_node: step1
nodes:
  step1:
    type: skill
    skill_name: echo
    inputs:
      message: "Hello, {workflow.inputs.name}!"
      uppercase: true
"""

    with gr.Column():
        gr.Markdown("## Workflow Runner")
        gr.Markdown("Define and execute multi-step workflows. Each step can call a different skill.")

        with gr.Row():
            with gr.Column(scale=2):
                workflow_editor = gr.Code(
                    value=load_example_workflow(),
                    language="yaml",
                    lines=20,
                    label="Workflow Definition (YAML)",
                )
            with gr.Column(scale=1):
                inputs_editor = gr.Code(
                    value='{\n  "name": "World"\n}',
                    language="json",
                    lines=10,
                    label="Inputs (JSON)",
                )

        with gr.Row():
            with gr.Column():
                run_btn = gr.Button("▶ Run Workflow", variant="primary", size="lg")
            with gr.Column():
                load_example_btn = gr.Button("📋 Load Example")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Output")
                output_display = gr.Code(language="json", lines=15, label="Result")

            with gr.Column():
                status_display = gr.Markdown("### Status")

        run_btn.click(
            fn=run_workflow_from_yaml,
            inputs=[workflow_editor, inputs_editor],
            outputs=[output_display, status_display],
        )

        load_example_btn.click(
            fn=load_example_workflow,
            outputs=workflow_editor,
        )

    return workflow_editor
