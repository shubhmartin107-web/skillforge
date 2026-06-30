import json


def process_json(data: str, query: str = "", pretty_print: bool = False) -> dict:
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "parsed": None,
            "formatted": "",
            "error": str(e),
        }

    result = parsed
    if query:
        try:
            import jmespath
            result = jmespath.search(query, parsed)
        except ImportError:
            result = {"error": "JMESPath not available", "data": parsed}

    if pretty_print:
        formatted = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        formatted = json.dumps(result, ensure_ascii=False)

    return {
        "valid": True,
        "parsed": result,
        "formatted": formatted,
        "error": "",
    }
