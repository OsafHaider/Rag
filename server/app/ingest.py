import io

from pypdf import PdfReader

from app import cache
from app.chunking import chunk_text
from app.config import settings
from app.db import get_conn
from app.embed import embed_passages


def extract_text(filename: str, data: bytes) -> str:
    """File ke bytes se plain text nikalta hai (text files + PDF)."""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    return data.decode("utf-8", errors="ignore")


def ingest_document(filename: str, data: bytes) -> tuple[int, int]:
    """
    Pura pipeline: text nikalo -> chunks -> embeddings -> DB mein save.
    Returns (document_id, chunks_count)
    """
    text = extract_text(filename, data).replace("\x00", "")
    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise ValueError("File mein koi readable text nahi mila")

    vectors = embed_passages(chunks)

    with get_conn() as conn:
        doc_id = conn.execute(
            "INSERT INTO documents (filename) VALUES (%s) RETURNING id",
            (filename,),
        ).fetchone()[0]

        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO chunks (document_id, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                [(doc_id, i, c, v) for i, (c, v) in enumerate(zip(chunks, vectors))],
            )

    # DB commit ho chuka hai, ab purane cached jawab invalid kar do
    cache.bump_version()

    return doc_id, len(chunks)