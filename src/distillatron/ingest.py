"""Pipeline orchestrator: manifest → scrape → embed → classify → store → update."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import lancedb
from openai import OpenAI

from .classify import classify_content
from .config import get_settings
from .db import Article, ensure_table
from .embed import embed_text
from .manifest import parse_manifest, update_manifest
from .scrape import scrape_url


def _extract_source(url: str) -> str:
    return urlparse(url).netloc


def _url_already_indexed(table: lancedb.table.Table, url: str) -> bool:
    try:
        results = table.search().where(f"url = '{url}'").limit(1).to_list()
        return len(results) > 0
    except Exception:
        return False


def process_manifest(
    manifest_path: Path | None = None,
    db: lancedb.DBConnection | None = None,
    deepseek_client: OpenAI | None = None,
) -> dict:
    settings = get_settings()

    if manifest_path is None:
        manifest_path = Path("manifest.md")

    if db is None:
        from .db import get_db

        db = get_db()

    if deepseek_client is None:
        deepseek_client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    table = ensure_table(db)

    entries = parse_manifest(manifest_path)
    counts = {"total": len(entries), "skipped": 0, "scraped": 0, "errors": 0}

    for entry in entries:
        if entry["status"] == "done":
            counts["skipped"] += 1
            continue

        url = entry["url"]

        if _url_already_indexed(table, url):
            update_manifest(manifest_path, url)
            counts["skipped"] += 1
            continue

        try:
            title, content = scrape_url(url, settings.firecrawl_api_key)
            embedding = embed_text(content[:8000])
            topics = classify_content(content, deepseek_client, settings.deepseek_model)

            article = Article(
                id=str(uuid.uuid4()),
                url=url,
                title=title,
                content=content,
                embedding=embedding,
                topics=topics,
                source=_extract_source(url),
                scraped_at=datetime.now(UTC),
            )

            table.add([article.model_dump()])
            update_manifest(manifest_path, url, title)
            counts["scraped"] += 1

        except Exception as e:
            print(f"ERROR processing {url}: {e}", file=__import__("sys").stderr)
            counts["errors"] += 1

    return counts


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "manifest.md"
    result = process_manifest(manifest_path=Path(path))
    print(
        f"Done. total={result['total']} skipped={result['skipped']} "
        f"scraped={result['scraped']} errors={result['errors']}"
    )
