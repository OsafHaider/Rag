"""
Redis cache layer.

Do cheezen cache hoti hain:
  1. Query embeddings  -> same sawal par embedding model dobara nahi chalta
  2. Final jawab (answer + sources) -> same sawal par na search hoti hai, na Groq call

Naya document upload hone par `bump_version()` chalta hai. Jawab ki cache key mein
yeh version shamil hai, is liye purane jawab khud bekaar ho jate hain (koi delete nahi karna parta).

Agar Redis band ho ya REDIS_URL khali ho, to cache chup chap skip hota hai
aur app bina cache ke normal chalti hai.
"""
import hashlib
import json
import logging
import re

import numpy as np
import redis

from app.config import settings

log = logging.getLogger("app.cache")

_client: redis.Redis | None = None


def _get() -> redis.Redis | None:
    global _client
    if not settings.cache_enabled or not settings.redis_url:
        return None
    if _client is None:
        _client = redis.Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.5,  # Redis down ho to request atke nahi
            socket_timeout=0.5,
        )
    return _client


def normalize(query: str) -> str:
    """'  Refund  POLICY? ' aur 'refund policy?' ek hi key banayen."""
    return re.sub(r"\s+", " ", query.strip().lower())


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


# ---------------- embeddings ----------------

def get_embedding(query: str) -> np.ndarray | None:
    r = _get()
    if r is None:
        return None
    key = f"emb:{settings.embed_model}:{_hash(normalize(query))}"
    try:
        raw = r.get(key)
    except redis.RedisError as e:
        log.warning("cache get_embedding failed: %s", e)
        return None
    if raw and len(raw) != settings.embed_dim * np.dtype(np.float32).itemsize:
        log.warning("cache get_embedding found invalid vector size; recomputing")
        return None
    return np.frombuffer(raw, dtype=np.float32) if raw else None


def set_embedding(query: str, vec: np.ndarray) -> None:
    r = _get()
    if r is None:
        return
    try:
        r.set(
            f"emb:{settings.embed_model}:{_hash(normalize(query))}",
            np.asarray(vec, dtype=np.float32).tobytes(),
            ex=settings.cache_ttl_seconds,
        )
    except redis.RedisError as e:
        log.warning("cache set_embedding failed: %s", e)


# ---------------- answers ----------------

def get_corpus_version() -> str | None:
    r = _get()
    if r is None:
        return None
    try:
        return _version(r)
    except redis.RedisError as e:
        log.warning("cache get_corpus_version failed: %s", e)
        return None


def _version(r: redis.Redis) -> str:
    v = r.get("corpus_version")
    return v.decode() if v else "0"


def _answer_key(version: str, query: str, document_id: int | None) -> str:
    scope = "all" if document_id is None else str(document_id)
    return f"ans:v{version}:{scope}:{_hash(normalize(query))}"


def get_answer(
    query: str, document_id: int | None, version: str | None
) -> dict | None:
    r = _get()
    if r is None or version is None:
        return None
    key = _answer_key(version, query, document_id)
    try:
        raw = r.get(key)
    except redis.RedisError as e:
        log.warning("cache get_answer failed: %s", e)
        return None
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("cache get_answer found invalid JSON; recomputing")
        return None
    if not isinstance(payload, dict):
        log.warning("cache get_answer found invalid payload; recomputing")
        return None
    return payload


def set_answer(
    query: str, document_id: int | None, payload: dict, version: str | None
) -> None:
    r = _get()
    if r is None or version is None:
        return
    try:
        r.set(
            _answer_key(version, query, document_id),
            json.dumps(payload),
            ex=settings.cache_ttl_seconds,
        )
    except redis.RedisError as e:
        log.warning("cache set_answer failed: %s", e)


def bump_version() -> None:
    """Naya document aaya: purane saare cached jawab invalid."""
    r = _get()
    if r is None:
        return
    try:
        r.incr("corpus_version")
    except redis.RedisError as e:
        log.warning("cache bump_version failed: %s", e)