def echo(message: str, uppercase: bool = False, prefix: str = "") -> dict:
    result = message
    if uppercase:
        result = result.upper()
    if prefix:
        result = f"{prefix}{result}"
    return {
        "result": result,
        "length": len(result),
    }
