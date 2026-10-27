from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector

from app.config import settings


@contextmanager
def get_conn():
    """Create a fresh connection for each request. Commit and close it when the block ends."""
    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)  # map the vector type to Python/numpy objects
        yield conn


def init_db() -> None:
    """Run on startup: create the extension, tables, and indexes if they do not exist."""
    # The extension must be created first; otherwise register_vector will not work
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id          SERIAL PRIMARY KEY,
                filename    TEXT NOT NULL,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id           SERIAL PRIMARY KEY,
                document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index  INTEGER NOT NULL,
                content      TEXT NOT NULL,
                embedding    vector({settings.embed_dim}) NOT NULL
            )
            """
        )
        # HNSW index: speeds up cosine similarity searches
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON chunks USING hnsw (embedding vector_cosine_ops)
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS chunks_document_idx ON chunks (document_id)"
        )