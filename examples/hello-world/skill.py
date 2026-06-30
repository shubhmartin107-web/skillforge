def run(name: str, greeting: str = "Hello") -> dict:
    message = f"{greeting}, {name}!"
    return {
        "message": message,
        "length": len(message),
    }
