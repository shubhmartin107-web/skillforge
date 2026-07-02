from __future__ import annotations

import json


def create_test_page():
    import gradio as gr

    from skillforge.models.execution import ExecutionRequest
    from skillforge.registry.local import LocalRegistry
    from skillforge.runtime.executor import Executor

    def get_skill_names() -> list[str]:
        reg = LocalRegistry()
        entries = reg.list_all()
        reg.close()
        return sorted(set(e.name for e in entries))

    def skill_selected(name: str):
        if not name:
            return "{}", ""

        reg = LocalRegistry()
        entry = reg.get(name)
        reg.close()

        if entry is None:
            return "{}", ""

        manifest_path = entry.manifest_path
        from pathlib import Path

        import yaml

        p = Path(manifest_path)
        if p.exists():
            raw = yaml.safe_load(p.read_text("utf-8"))
            inputs = {}
            for inp in raw.get("inputs", []):
                default = inp.get("default", "")
                inputs[inp["name"]] = default
            return json.dumps(inputs, indent=2), entry.description
        return "{}", ""

    def run_skill(name: str, inputs_json: str, use_sandbox: bool):
        if not name:
            return "Select a skill first", ""
        try:
            inputs = json.loads(inputs_json)
        except json.JSONDecodeError as e:
            return f"Invalid JSON inputs: {e}", ""

        req = ExecutionRequest(skill_name=name, inputs=inputs)
        executor = Executor()

        try:
            result = executor.execute_in_sandbox(req) if use_sandbox else executor.execute(req)
        except Exception as e:
            return f"Execution error: {e}", ""

        if result.success:
            output_json = json.dumps(result.outputs, indent=2)
            events_json = json.dumps(result.events[-5:], indent=2) if result.events else "[]"
            return output_json, events_json
        else:
            return f"Error: {result.error}", ""

    with gr.Column():
        skill_dropdown = gr.Dropdown(
            choices=get_skill_names(),
            label="Select Skill",
            interactive=True,
        )
        sandbox_checkbox = gr.Checkbox(label="Run in sandbox", value=False)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Inputs (JSON)")
            inputs_editor = gr.Code(
                value="{}",
                language="json",
                lines=8,
            )
            run_btn = gr.Button("Run Skill", variant="primary")

        with gr.Column():
            gr.Markdown("### Output")
            output_display = gr.Code(language="json", lines=8)

    with gr.Row():
        skill_description = gr.Markdown("### Description")

    events_display = gr.JSON(label="Recent Events")

    skill_dropdown.change(
        fn=skill_selected,
        inputs=skill_dropdown,
        outputs=[inputs_editor, skill_description],
    )

    run_btn.click(
        fn=run_skill,
        inputs=[skill_dropdown, inputs_editor, sandbox_checkbox],
        outputs=[output_display, events_display],
    )

    return skill_dropdown
