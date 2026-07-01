from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .db import ensure_table, get_db
from .routes import router
from .web.routes import router as web_router


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

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "web" / "static"), name="static")
app.include_router(web_router)
app.include_router(router)
