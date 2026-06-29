from __future__ import annotations

import lancedb
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .db import ArticleSummary, get_db
from .search import search as semantic_search

router = APIRouter()


class SearchResponse(BaseModel):
    results: list[dict]
    query: str
    count: int


class ArticleListResponse(BaseModel):
    articles: list[ArticleSummary]
    total: int
    limit: int
    offset: int


class BuildResponse(BaseModel):
    status: str
    counts: dict


class TopicsResponse(BaseModel):
    topics: list[dict]  # [{name: str, count: int}, ...]


def _get_db() -> lancedb.DBConnection:
    return get_db()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    topic: str | None = Query(None, description="Filter by topic"),
    limit: int = Query(10, ge=1, le=100),
    db: lancedb.DBConnection = Depends(_get_db),
) -> SearchResponse:
    try:
        results = semantic_search(q, db, topic=topic, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return SearchResponse(results=results, query=q, count=len(results))


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    topic: str | None = Query(None, description="Filter by topic"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: lancedb.DBConnection = Depends(_get_db),
) -> ArticleListResponse:
    try:
        table = db.open_table("articles")
        all_rows = table.search().limit(10000).to_list()
    except Exception:
        return ArticleListResponse(articles=[], total=0, limit=limit, offset=offset)

    if topic:
        topic_lower = topic.lower()
        all_rows = [r for r in all_rows if topic_lower in [t.lower() for t in r.get("topics", [])]]

    total = len(all_rows)
    page = all_rows[offset : offset + limit]
    summaries = [
        ArticleSummary(
            id=r["id"],
            url=r["url"],
            title=r["title"],
            topics=r.get("topics", []),
            source=r.get("source", ""),
            scraped_at=r.get("scraped_at"),
        )
        for r in page
    ]

    return ArticleListResponse(articles=summaries, total=total, limit=limit, offset=offset)


@router.get("/articles/{article_id}")
async def get_article(
    article_id: str,
    db: lancedb.DBConnection = Depends(_get_db),
) -> dict:
    try:
        table = db.open_table("articles")
        results = table.search().where(f"id = '{article_id}'").limit(1).to_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not results:
        raise HTTPException(status_code=404, detail="Article not found")

    return results[0]


@router.get("/topics", response_model=TopicsResponse)
async def list_topics(
    db: lancedb.DBConnection = Depends(_get_db),
) -> TopicsResponse:
    try:
        table = db.open_table("articles")
        rows = table.search().limit(10000).to_list()
    except Exception:
        return TopicsResponse(topics=[])

    counts: dict[str, int] = {}
    for row in rows:
        for topic in row.get("topics", []):
            counts[topic] = counts.get(topic, 0) + 1

    topics = [{"name": k, "count": v} for k, v in sorted(counts.items())]
    return TopicsResponse(topics=topics)


@router.post("/build", response_model=BuildResponse)
async def trigger_build() -> BuildResponse:
    from .ingest import process_manifest

    try:
        counts = process_manifest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return BuildResponse(status="complete", counts=counts)
