from __future__ import annotations

from skillforge.registry.local import LocalRegistry


def create_stats_page():
    import gradio as gr

    reg = LocalRegistry()
    stats = reg.stats()
    all_skills = reg.list_all()
    reg.close()

    tag_counts: dict[str, int] = {}
    cat_counts: dict[str, int] = {}
    for s in all_skills:
        for t in s.tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
        for c in s.categories:
            cat_counts[c] = cat_counts.get(c, 0) + 1

    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:10]
    top_cats = sorted(cat_counts.items(), key=lambda x: -x[1])[:10]

    mode_counts: dict[str, int] = {}
    for s in all_skills:
        mode_counts[s.execution_mode] = mode_counts.get(s.execution_mode, 0) + 1

    tags_html = "".join(
        f'<span style="display:inline-block;background:var(--primary-100);padding:2px 8px;border-radius:12px;margin:2px">{t} ({c})</span> '
        for t, c in top_tags
    ) or "<em>None</em>"

    cats_html = "".join(
        f'<span style="display:inline-block;background:var(--secondary-100);padding:2px 8px;border-radius:12px;margin:2px">{c} ({n})</span> '
        for c, n in top_cats
    ) or "<em>None</em>"

    modes_html = "".join(
        f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;margin:2px;background:#e0e7ff">{m}: {n}</span> '
        for m, n in sorted(mode_counts.items())
    ) or "<em>None</em>"

    with gr.Column():
        gr.Markdown("## Registry Overview")

        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML(
                    f'<div class="stat-card"><div class="stat-number">{stats.total_skills}</div>'
                    f'<div class="stat-label">Skills Installed</div></div>'
                )
            with gr.Column(scale=1):
                gr.HTML(
                    f'<div class="stat-card"><div class="stat-number">{stats.total_authors}</div>'
                    f'<div class="stat-label">Authors</div></div>'
                )
            with gr.Column(scale=1):
                gr.HTML(
                    f'<div class="stat-card"><div class="stat-number">{stats.total_tags}</div>'
                    f'<div class="stat-label">Tags</div></div>'
                )
            with gr.Column(scale=1):
                gr.HTML(
                    f'<div class="stat-card"><div class="stat-number">{stats.total_categories}</div>'
                    f'<div class="stat-label">Categories</div></div>'
                )

        with gr.Row():
            with gr.Column():
                gr.Markdown(f"### Top Tags\n{tags_html}")
            with gr.Column():
                gr.Markdown(f"### Top Categories\n{cats_html}")

        gr.Markdown(f"### Execution Modes\n{modes_html}")
        gr.Markdown(f"**Last Updated:** {stats.last_updated.isoformat() if stats.last_updated else 'N/A'}")
