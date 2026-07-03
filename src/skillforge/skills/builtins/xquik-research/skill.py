from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import httpx

BASE_URL = "https://xquik.com"


def query_xquik(
    endpoint: str,
    api_key: str,
    query: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    start = time.time()
    path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    url = urljoin(BASE_URL, path)

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                url,
                params=query or {},
                headers={"X-API-Key": api_key, "Accept": "application/json"},
            )

        elapsed = int((time.time() - start) * 1000)
        try:
            data: Any = response.json()
            body = ""
        except ValueError:
            data = {}
            body = response.text[:10000]

        return {
            "status_code": response.status_code,
            "data": data,
            "body": body,
            "elapsed_ms": elapsed,
        }
    except httpx.TimeoutException:
        return {
            "status_code": 0,
            "data": {},
            "body": "",
            "elapsed_ms": timeout * 1000,
            "error": "Request timed out",
        }
    except Exception as exc:
        return {
            "status_code": 0,
            "data": {},
            "body": "",
            "elapsed_ms": int((time.time() - start) * 1000),
            "error": str(exc),
        }
