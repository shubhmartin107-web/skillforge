from pathlib import Path


def read_file(path: str, encoding: str = "utf-8", max_bytes: int = 1048576) -> dict:
    file_path = Path(path).resolve()

    if not file_path.exists():
        return {
            "error": f"File not found: {path}",
            "content": "",
            "size_bytes": 0,
            "truncated": False,
        }
    if not file_path.is_file():
        return {"error": f"Not a file: {path}", "content": "", "size_bytes": 0, "truncated": False}

    size = file_path.stat().st_size
    truncated = size > max_bytes

    try:
        content = file_path.read_text(encoding)[:max_bytes]
    except UnicodeDecodeError:
        content = f"<binary file, {size} bytes>"

    return {
        "content": content,
        "size_bytes": size,
        "truncated": truncated,
    }
