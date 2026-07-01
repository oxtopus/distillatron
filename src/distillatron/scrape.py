from __future__ import annotations

from firecrawl.v1 import V1FirecrawlApp


def scrape_url(url: str, api_key: str) -> tuple[str, str]:
    """Scrape a URL and return (title, markdown_content).

    Uses Firecrawl to handle JavaScript-rendered pages and return clean markdown.
    """
    app = V1FirecrawlApp(api_key=api_key)
    result = app.scrape_url(url, formats=["markdown"])
    metadata = result.metadata or {}
    title = metadata.get("title") or metadata.get("og:title") or url
    content = result.markdown or ""
    return title, content
