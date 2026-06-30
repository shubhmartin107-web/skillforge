import math


def calculate(a: float, b: float, operation: str = "add") -> dict:
    ops = {
        "add": lambda: a + b,
        "sub": lambda: a - b,
        "mul": lambda: a * b,
        "div": lambda: a / b if b != 0 else float("inf"),
        "pow": lambda: math.pow(a, b),
        "mod": lambda: a % b if b != 0 else float("inf"),
    }
    fn = ops.get(operation)
    if fn is None:
        return {"error": f"Unknown operation: {operation}", "result": None}
    return {"result": fn(), "operation": operation}
