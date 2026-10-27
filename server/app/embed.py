import numpy as np
from fastembed import TextEmbedding

from app.config import settings

_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    """Load the model only on first use (download + memory), then reuse it."""
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=settings.embed_model)
    return _model


def embed_passages(texts: list[str]) -> list[np.ndarray]:
    """Convert document chunks into vectors."""
    model = get_model()
    return [np.asarray(v, dtype=np.float32) for v in model.passage_embed(texts)]


def embed_query(query: str) -> np.ndarray:
    """Convert the user's query into a vector (bge models use a separate query prefix)."""
    model = get_model()
    return np.asarray(next(iter(model.query_embed(query))), dtype=np.float32)