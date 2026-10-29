import io

from pypdf import PdfReader

from app import cache
from app.chunking import chunk_text
from app.config import settings
from app.db import get_conn
from app.embed import embed_passages


def extract_text(filename: str, data: bytes) -> str:
    """Extract plain text from file bytes (text files and PDFs)."""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    return data.decode("utf-8", errors="ignore")


def ingest_document(filename: str, data: bytes) -> tuple[int, int]:
    """
    Process the document: extract text, create chunks and embeddings, and save them to the database.
    Returns (document_id, chunks_count)
    """
    text = extract_text(filename, data).replace("\x00", "")
    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise ValueError("The uploaded file contains no readable text.")

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

    # The database transaction has committed; invalidate cached answers.
    cache.bump_version()

    return doc_id, len(chunks)