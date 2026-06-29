from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import ensure_table, get_db
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    ensure_table(db)
    yield


app = FastAPI(
    title="Distillatron",
    description="News article indexing and semantic search",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
