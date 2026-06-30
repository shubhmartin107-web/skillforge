from __future__ import annotations

from skillforge.config import settings
from skillforge.dashboard.pages.audit import create_audit_page
from skillforge.dashboard.pages.browse import create_browse_page
from skillforge.dashboard.pages.inspect import create_inspect_page
from skillforge.dashboard.pages.stats import create_stats_page
from skillforge.dashboard.pages.test import create_test_page
from skillforge.dashboard.pages.workflows import create_workflows_page


def create_app():
    try:
        import gradio as gr
    except ImportError:
        print("gradio not installed. Install with: pip install skillforge[dashboard]")
        return None

    from skillforge._version import __version__

    custom_css = """
    .skill-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin: 8px; }
    .skill-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.12); transition: box-shadow 0.2s; }
    .stat-card { text-align: center; padding: 20px; background: var(--background-fill-primary); border-radius: 12px; border: 1px solid var(--border-color-primary); }
    .stat-number { font-size: 2.5em; font-weight: 700; color: var(--primary-500); }
    .stat-label { font-size: 0.9em; color: var(--text-color-secondary); margin-top: 4px; }
    .error-text { color: #ef4444; }
    .success-text { color: #22c55e; }
    """

    with gr.Blocks(
        title=f"SkillForge Dashboard v{__version__}",
        theme="soft",
        css=custom_css,
    ) as demo:
        gr.Markdown(
            f"# ⚒ SkillForge Dashboard  `v{__version__}`\n"
            "### Browse, inspect, test, and compose your agent skills"
        )

        with gr.Tabs():
            with gr.TabItem("📊 Overview"):
                create_stats_page()

            with gr.TabItem("🔍 Browse"):
                create_browse_page()

            with gr.TabItem("📋 Inspect"):
                create_inspect_page()

            with gr.TabItem("🧪 Test"):
                create_test_page()

            with gr.TabItem("🔄 Workflows"):
                create_workflows_page()

            with gr.TabItem("📜 Audit Log"):
                create_audit_page()

        gr.Markdown(
            f"---\n"
            f"<div style='text-align: center; color: var(--text-color-secondary); font-size: 0.85em;'>"
            f"SkillForge v{__version__} | "
            f"<a href='https://github.com/shubhmartin107-web/skillforge' target='_blank'>GitHub</a> | "
            f"<a href='https://github.com/shubhmartin107-web/skillforge/issues' target='_blank'>Report Issue</a> | "
            f"Apache 2.0 License"
            f"</div>"
        )

    return demo


def run_dashboard(host: str | None = None, port: int | None = None):
    demo = create_app()
    if demo is None:
        return
    demo.launch(
        server_name=host or settings.dashboard_host,
        server_port=port or settings.dashboard_port,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    run_dashboard()
