import re


def render_template(
    template: str, variables: dict | None = None, missing_placeholder: str = "keep"
) -> dict:
    variables = variables or {}
    pattern = r"\{(\w+)\}"
    placeholders = re.findall(pattern, template)
    replaced = 0

    def replacer(match):
        nonlocal replaced
        key = match.group(1)
        if key in variables:
            replaced += 1
            return str(variables[key])
        if missing_placeholder == "empty":
            return ""
        if missing_placeholder == "error":
            return match.group(0)
        return match.group(0)

    result = re.sub(pattern, replacer, template)
    errors = []
    if missing_placeholder == "error":
        for ph in placeholders:
            if ph not in variables:
                errors.append(f"Missing variable: {{{ph}}}")

    return {
        "result": result,
        "placeholders_found": len(placeholders),
        "placeholders_replaced": replaced,
        "errors": errors if errors else None,
    }
