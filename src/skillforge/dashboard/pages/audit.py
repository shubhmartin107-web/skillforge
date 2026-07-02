from __future__ import annotations

import json

from skillforge.security.audit import AuditLogger


def create_audit_page():
    import gradio as gr

    def refresh_audit(limit: int) -> str:
        audit = AuditLogger()
        entries = audit.get_recent(limit=limit)
        if not entries:
            return "No audit log entries found."
        return json.dumps(entries, indent=2, default=str)

    with gr.Column():
        gr.Markdown("## Audit Log")
        gr.Markdown(
            "Recent skill execution events. Sensitive data (keys, tokens) is automatically redacted."
        )

        with gr.Row():
            limit_input = gr.Number(
                value=50, label="Entries to show", minimum=1, maximum=500, step=1
            )
            refresh_btn = gr.Button("🔄 Refresh", variant="primary")

        audit_output = gr.Code(
            value=refresh_audit(50),
            language="json",
            lines=20,
            label="Audit Log Entries",
        )

        refresh_btn.click(
            fn=lambda limit: refresh_audit(int(limit)),
            inputs=limit_input,
            outputs=audit_output,
        )

    return audit_output
