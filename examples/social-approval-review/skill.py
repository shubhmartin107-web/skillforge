from __future__ import annotations

ACCOUNT_ACTIONS = {
    "draft",
    "publish",
    "reply",
    "follow",
    "dm",
    "delete",
    "giveaway",
    "media_upload",
    "webhook",
    "account_setting",
}

STATE_CHANGING_ACTIONS = ACCOUNT_ACTIONS - {"draft"}


def _normalize_actions(requested_actions: list[str] | str | None) -> list[str]:
    if requested_actions is None:
        return []

    if isinstance(requested_actions, str):
        raw_actions = requested_actions.replace(",", " ").split()
    else:
        raw_actions = requested_actions

    normalized: list[str] = []
    for action in raw_actions:
        key = action.strip().lower().replace("-", "_")
        if key in ACCOUNT_ACTIONS and key not in normalized:
            normalized.append(key)

    return normalized


def _detect_actions(workflow_summary: str) -> list[str]:
    text = workflow_summary.lower().replace("-", "_")
    return [action for action in sorted(ACCOUNT_ACTIONS) if action in text]


def run(
    workflow_summary: str,
    requested_actions: list[str] | str | None = None,
    has_human_approval: bool = False,
) -> dict:
    summary = workflow_summary.strip()
    actions = _normalize_actions(requested_actions)

    if not actions and summary:
        actions = _detect_actions(summary)

    approval_required = any(action in STATE_CHANGING_ACTIONS for action in actions)
    missing_context: list[str] = []

    if not summary:
        missing_context.append("workflow_summary")

    if approval_required and not has_human_approval:
        missing_context.append("human_approval")

    if approval_required and not actions:
        missing_context.append("requested_actions")

    if not summary:
        decision = "blocked"
    elif missing_context:
        decision = "needs_changes"
    else:
        decision = "approved"

    return {
        "decision": decision,
        "approval_required": approval_required,
        "actions": actions,
        "missing_context": missing_context,
    }
