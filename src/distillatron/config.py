from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

EMBEDDING_DIMS: dict[str, int] = {
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    firecrawl_api_key: str
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    lancedb_uri: str = "data/lancedb"

    embedding_backend: str = "openai"
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"

    def embedding_dim(self) -> int:
        if self.embedding_backend == "local":
            return EMBEDDING_DIMS.get(self.local_embedding_model, 384)
        return EMBEDDING_DIMS.get(self.openai_embedding_model, 1536)


@lru_cache
def get_settings() -> Settings:
    return Settings()
