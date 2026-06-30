from datetime import UTC, datetime, timedelta


def datetime_operation(
    operation: str = "now",
    date_string: str = "",
    format: str = "%Y-%m-%d %H:%M:%S",
    input_format: str = "%Y-%m-%d",
    days: int = 0,
    timezone: str = "UTC",
) -> dict:
    ops = {
        "now": _now,
        "format": _format_date,
        "parse": _parse_date,
        "diff": _date_diff,
        "add_days": _add_days,
    }

    fn = ops.get(operation)
    if fn is None:
        return {
            "result": f"Unknown operation: {operation}",
            "timestamp": None,
            "iso_string": None,
        }

    return fn(date_string=date_string, fmt=format, input_fmt=input_format, days=days)


def _now(**kwargs) -> dict:
    now = datetime.now(UTC)
    return {
        "result": now.strftime(kwargs.get("fmt", "%Y-%m-%d %H:%M:%S")),
        "timestamp": now.timestamp(),
        "iso_string": now.isoformat(),
    }


def _format_date(**kwargs) -> dict:
    try:
        dt = datetime.strptime(kwargs["date_string"], kwargs["input_fmt"])
        return {
            "result": dt.strftime(kwargs["fmt"]),
            "timestamp": dt.timestamp(),
            "iso_string": dt.isoformat(),
        }
    except ValueError as e:
        return {"result": f"Parse error: {e}", "timestamp": None, "iso_string": None}


def _parse_date(**kwargs) -> dict:
    try:
        dt = datetime.strptime(kwargs["date_string"], kwargs["input_fmt"])
        return {
            "result": dt.isoformat(),
            "timestamp": dt.timestamp(),
            "iso_string": dt.isoformat(),
        }
    except ValueError as e:
        return {"result": f"Parse error: {e}", "timestamp": None, "iso_string": None}


def _date_diff(**kwargs) -> dict:
    try:
        dt1 = datetime.strptime(kwargs["date_string"], kwargs["input_fmt"])
        dt2 = datetime.now(UTC).replace(tzinfo=None)
        diff = dt2 - dt1
        return {
            "result": str(diff),
            "timestamp": diff.total_seconds(),
            "iso_string": None,
        }
    except ValueError as e:
        return {"result": f"Error: {e}", "timestamp": None, "iso_string": None}


def _add_days(**kwargs) -> dict:
    try:
        if kwargs["date_string"]:
            dt = datetime.strptime(kwargs["date_string"], kwargs["input_fmt"])
        else:
            dt = datetime.now()
        result = dt + timedelta(days=kwargs["days"])
        return {
            "result": result.strftime(kwargs["fmt"]),
            "timestamp": result.timestamp(),
            "iso_string": result.isoformat(),
        }
    except ValueError as e:
        return {"result": f"Error: {e}", "timestamp": None, "iso_string": None}
