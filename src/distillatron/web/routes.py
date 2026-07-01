from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from ..db import get_db
from ..search import search as semantic_search

TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)


def _render(name: str, request: Request, **kwargs) -> HTMLResponse:
    template = _jinja_env.get_template(name)
    return HTMLResponse(template.render(request=request, **kwargs))


router = APIRouter()


def _get_db():
    return get_db()


def _count_topics(db) -> list[dict]:
    try:
        table = db.open_table("articles")
        rows = table.search().limit(10000).to_list()
    except Exception:
        return []
    counts: dict[str, int] = {}
    for row in rows:
        for topic in row.get("topics", []):
            counts[topic] = counts.get(topic, 0) + 1
    return [{"name": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


@router.get("/", response_class=HTMLResponse)
async def browse(request: Request) -> HTMLResponse:
    return _render("browse.html", request)


@router.get("/web/topics", response_class=HTMLResponse)
async def topic_list(
    request: Request,
    db=Depends(_get_db),
) -> HTMLResponse:
    topics = _count_topics(db)
    try:
        table = db.open_table("articles")
        total = table.count_rows()
    except Exception:
        total = 0
    return _render(
        "topic_list.html",
        request,
        topics=topics,
        total=total,
    )


@router.get("/web/articles", response_class=HTMLResponse)
async def article_list(
    request: Request,
    topic: str | None = Query(None),
    db=Depends(_get_db),
) -> HTMLResponse:
    try:
        table = db.open_table("articles")
        rows = table.search().limit(10000).to_list()
    except Exception:
        rows = []

    if topic:
        topic_lower = topic.lower()
        rows = [r for r in rows if topic_lower in [t.lower() for t in r.get("topics", [])]]

    articles = [
        {
            "id": r["id"],
            "url": r["url"],
            "title": r["title"],
            "topics": ", ".join(r.get("topics", [])),
            "source": r.get("source", ""),
            "scraped_at": str(r.get("scraped_at", ""))[:19] if r.get("scraped_at") else "",
        }
        for r in rows
    ]
    return _render(
        "article_list.html",
        request,
        articles=articles,
        topic=topic,
        total=len(articles),
    )


@router.get("/web/search", response_class=HTMLResponse)
async def web_search(
    request: Request,
    q: str = Query(..., min_length=1),
    topic: str | None = Query(None),
    db=Depends(_get_db),
) -> HTMLResponse:
    try:
        results = semantic_search(q, db, topic=topic, limit=30)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    articles = [
        {
            "id": r["id"],
            "url": r["url"],
            "title": r["title"],
            "topics": ", ".join(r.get("topics", [])),
            "source": r.get("source", ""),
            "scraped_at": str(r.get("scraped_at", ""))[:19] if r.get("scraped_at") else "",
        }
        for r in results
    ]
    return _render(
        "search_results.html",
        request,
        articles=articles,
        query=q,
        total=len(articles),
    )


@router.get("/web/articles/{article_id}", response_class=HTMLResponse)
async def article_detail(
    request: Request,
    article_id: str,
    db=Depends(_get_db),
) -> HTMLResponse:
    try:
        table = db.open_table("articles")
        results = table.search().where(f"id = '{article_id}'").limit(1).to_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not results:
        raise HTTPException(status_code=404, detail="Article not found")

    r = results[0]
    article = {
        "id": r["id"],
        "url": r["url"],
        "title": r["title"],
        "content": r.get("content", ""),
        "topics": r.get("topics", []),
        "source": r.get("source", ""),
        "scraped_at": str(r.get("scraped_at", ""))[:19] if r.get("scraped_at") else "",
    }
    return _render(
        "article.html",
        request,
        article=article,
    )
