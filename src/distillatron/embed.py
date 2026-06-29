from __future__ import annotations

from fastembed import TextEmbedding
from openai import OpenAI

from .config import get_settings

_local_model: TextEmbedding | None = None
_local_model_name: str | None = None


def _get_local_model(model_name: str) -> TextEmbedding:
    global _local_model, _local_model_name
    if _local_model is None or _local_model_name != model_name:
        _local_model = TextEmbedding(model_name=model_name)
        _local_model_name = model_name
    return _local_model


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.embedding_backend == "local":
        model = _get_local_model(settings.local_embedding_model)
        vec = next(model.embed([text]))
        return vec.tolist()

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when EMBEDDING_BACKEND=openai")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=settings.openai_embedding_model, input=text)
    return response.data[0].embedding
