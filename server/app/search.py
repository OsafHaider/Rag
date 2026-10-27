from app.config import settings
from app.db import get_conn
from app.embed import embed_query


def search_chunks(
    query: str, top_k: int | None = None, document_id: int | None = None
) -> list[dict]:
    """
    Embed the query and retrieve the most relevant chunks from the database.
    `<=>` is the pgvector cosine distance operator (lower = more similar).
    """
    top_k = top_k or settings.top_k
    qvec = embed_query(query)

    where = "WHERE c.document_id = %s" if document_id is not None else ""
    sql = f"""
        SELECT c.content, d.filename, 1 - (c.embedding <=> %s) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        {where}
        ORDER BY c.embedding <=> %s
        LIMIT %s
    """

    params: list = [qvec]
    if document_id is not None:
        params.append(document_id)
    params += [qvec, top_k]

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [
        {"content": content, "filename": filename, "score": float(score)}
        for content, filename, score in rows
    ]