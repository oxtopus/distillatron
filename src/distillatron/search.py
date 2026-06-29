from __future__ import annotations

import lancedb

from .embed import embed_text


def search(
    query: str,
    db: lancedb.DBConnection,
    topic: str | None = None,
    limit: int = 10,
) -> list[dict]:
    query_embedding = embed_text(query)
    table = db.open_table("articles")
    results = table.search(query_embedding).limit(limit * 2).to_list()

    if topic:
        topic_lower = topic.lower()
        results = [r for r in results if topic_lower in [t.lower() for t in r.get("topics", [])]]

    return results[:limit]
