from __future__ import annotations

from datetime import datetime

import lancedb
from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel

from .config import get_settings


class Article(LanceModel):
    id: str
    url: str
    title: str
    content: str
    embedding: Vector(get_settings().embedding_dim())
    topics: list[str]
    source: str
    scraped_at: datetime


class ArticleSummary(BaseModel):
    id: str
    url: str
    title: str
    topics: list[str]
    source: str
    scraped_at: datetime


def get_db(uri: str | None = None) -> lancedb.DBConnection:
    settings = get_settings()
    db_uri = uri or settings.lancedb_uri
    return lancedb.connect(db_uri)


def ensure_table(db: lancedb.DBConnection) -> lancedb.table.Table:
    if "articles" in db.table_names():
        return db.open_table("articles")
    return db.create_table("articles", schema=Article)
