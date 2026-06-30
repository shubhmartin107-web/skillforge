from __future__ import annotations

from pathlib import Path


def create_inspect_page():
    import gradio as gr
    import yaml

    from skillforge.models.skill import SkillManifest
    from skillforge.registry.local import LocalRegistry

    def get_skill_names() -> list[str]:
        reg = LocalRegistry()
        entries = reg.list_all()
        reg.close()
        return sorted(set(e.name for e in entries))

    def inspect_skill(name: str) -> tuple[str, str, str, str, str]:
        if not name:
            return ("", "", "", "", "")

        reg = LocalRegistry()
        entry = reg.get(name)
        reg.close()

        if entry is None:
            return ("Not found", "", "", "", "")

        manifest_path = Path(entry.manifest_path)
        if not manifest_path.exists():
            return (entry.name, entry.version, entry.description, "", "No manifest file found")

        raw = yaml.safe_load(manifest_path.read_text("utf-8"))
        try:
            manifest = SkillManifest.from_yaml_dict(raw)
        except Exception as e:
            return (entry.name, entry.version, entry.description, "", f"Parse error: {e}")

        inputs_str = "\n".join(
            f"  - {i.name} ({i.type}){' required' if i.required else ''}: {i.description}"
            for i in manifest.inputs
        ) or "  (none)"

        outputs_str = "\n".join(
            f"  - {o.name} ({o.type}): {o.description}"
            for o in manifest.outputs
        ) or "  (none)"

        details = (
            f"**Author**: {manifest.author.name}\n"
            f"**License**: {manifest.license or 'None'}\n"
            f"**Execution Mode**: {manifest.execution.get('mode', 'direct')}\n"
            f"**Entrypoint**: {manifest.execution.get('entrypoint', 'skill.py')}\n"
            f"**Runtime**: {manifest.execution.get('runtime', 'python3.12')}\n"
            f"**Network**: {'Yes' if manifest.permissions.network else 'No'}\n"
            f"**Dangerous**: {'Yes' if manifest.permissions.dangerous else 'No'}\n"
            f"**Tags**: {', '.join(manifest.tags)}\n"
            f"**Categories**: {', '.join(manifest.categories)}\n"
            f"**Dependencies**: {', '.join(d.name for d in manifest.dependencies) or 'None'}\n"
        )

        return (entry.name, entry.version, entry.description, details,
                f"### Inputs\n{inputs_str}\n\n### Outputs\n{outputs_str}")

    with gr.Column():
        skill_dropdown = gr.Dropdown(
            choices=get_skill_names(),
            label="Select Skill",
            interactive=True,
        )
        refresh_btn = gr.Button("Refresh List")

    with gr.Column():
        name_display = gr.Markdown("### Name")
        version_display = gr.Markdown("**Version**: ")
        description_display = gr.Markdown("**Description**: ")

    with gr.Row():
        with gr.Column():
            details_display = gr.Markdown("### Details")

        with gr.Column():
            io_display = gr.Markdown("### Inputs / Outputs")

    skill_dropdown.change(
        fn=inspect_skill,
        inputs=skill_dropdown,
        outputs=[name_display, version_display, description_display, details_display, io_display],
    )

    def refresh_list():
        return {"choices": get_skill_names(), "__type__": "update"}

    refresh_btn.click(
        fn=refresh_list,
        outputs=skill_dropdown,
    )

    return skill_dropdown
