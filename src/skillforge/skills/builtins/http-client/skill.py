def http_request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: str = "",
    timeout: int = 30,
) -> dict:
    import time

    import httpx

    headers = headers or {}
    start = time.time()

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                content=body if body else None,
            )

        elapsed = int((time.time() - start) * 1000)
        response_body = response.text[:10000]

        return {
            "status_code": response.status_code,
            "body": response_body,
            "headers": dict(response.headers),
            "elapsed_ms": elapsed,
        }

    except httpx.TimeoutException:
        return {
            "status_code": 0,
            "body": "",
            "headers": {},
            "elapsed_ms": timeout * 1000,
            "error": "Request timed out",
        }
    except Exception as e:
        return {
            "status_code": 0,
            "body": "",
            "headers": {},
            "elapsed_ms": int((time.time() - start) * 1000),
            "error": str(e),
        }
