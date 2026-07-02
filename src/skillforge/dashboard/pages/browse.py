from __future__ import annotations

from skillforge.models.registry import SearchQuery
from skillforge.registry.local import LocalRegistry


def create_browse_page():
    import gradio as gr

    reg = LocalRegistry()
    stats = reg.stats()
    reg.close()

    def search_skills(query: str, tag: str) -> list[list[str | int]]:
        reg = LocalRegistry()
        q = SearchQuery(query=query)
        if tag:
            q.tags = [tag]
        result = reg.search(q)
        reg.close()

        rows = []
        for entry in result.entries:
            rows.append(
                [
                    entry.name,
                    entry.version,
                    entry.description[:60],
                    entry.author_name,
                    ", ".join(entry.tags[:3]),
                    entry.execution_mode,
                ]
            )
        return rows

    def get_all_tags() -> list[str]:
        reg = LocalRegistry()
        entries = reg.list_all()
        reg.close()
        tags = set()
        for e in entries:
            tags.update(e.tags)
        return [""] + sorted(tags)

    with gr.Column():
        gr.Markdown(
            f"**{stats.total_skills} skills installed** | {stats.total_categories} categories"
        )

        with gr.Row():
            search_input = gr.Textbox(label="Search", placeholder="Search skills...", scale=3)
            tag_filter = gr.Dropdown(
                choices=get_all_tags(),
                label="Tag Filter",
                value="",
                scale=1,
            )

        refresh_btn = gr.Button("Search", variant="primary")

    skill_table = gr.Dataframe(
        headers=["Name", "Version", "Description", "Author", "Tags", "Mode"],
        label="Installed Skills",
        interactive=False,
        column_widths=[150, 80, 300, 120, 150, 80],
    )

    refresh_btn.click(
        fn=search_skills,
        inputs=[search_input, tag_filter],
        outputs=skill_table,
    )
    search_input.submit(
        fn=search_skills,
        inputs=[search_input, tag_filter],
        outputs=skill_table,
    )

    return skill_table
