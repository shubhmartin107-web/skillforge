import re
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._text.append(data.strip())

    def get_text(self):
        return " ".join(t for t in self._text if t)


def _extract_links(html: str, base_url: str) -> list[str]:
    links = []
    pattern = r'href=["\'](https?://[^"\']+)["\']'
    for match in re.finditer(pattern, html, re.IGNORECASE):
        links.append(match.group(1))
    return links


def fetch_page(url: str, extract_links: bool = False, max_chars: int = 5000) -> dict:
    import httpx

    try:
        resp = httpx.get(url, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()

        html = resp.text
        extractor = _TextExtractor()
        extractor.feed(html)
        content = extractor.get_text()[:max_chars]

        result = {
            "content": content,
            "status_code": resp.status_code,
        }

        if extract_links:
            result["links"] = _extract_links(html, url)[:50]

        return result

    except httpx.HTTPStatusError as e:
        return {"content": "", "status_code": e.response.status_code, "error": str(e)}
    except Exception as e:
        return {"content": "", "status_code": 0, "error": str(e)}
