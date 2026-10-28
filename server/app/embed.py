import numpy as np
from fastembed import TextEmbedding

from app import cache
from app.config import settings

_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    """Model sirf pehli dafa load hota hai (download + memory), phir reuse."""
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=settings.embed_model)
    return _model


def embed_passages(texts: list[str]) -> list[np.ndarray]:
    """Document chunks ko vectors mein badalta hai."""
    model = get_model()
    return [np.asarray(v, dtype=np.float32) for v in model.passage_embed(texts)]


def embed_query(query: str) -> np.ndarray:
    """User ki query ko vector mein badalta hai (bge models query ke liye alag prefix use karte hain)."""
    cached = cache.get_embedding(query)
    if cached is not None:
        return cached

    model = get_model()
    vec = np.asarray(next(iter(model.query_embed(query))), dtype=np.float32)
    cache.set_embedding(query, vec)
    return vec