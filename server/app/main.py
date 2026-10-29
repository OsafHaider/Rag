from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import cache
from app.config import settings
from app.db import init_db
from app.embed import get_model
from app.ingest import ingest_document
from app.llm import generate_answer
from app.search import search_chunks

ALLOWED_EXT = (".txt", ".md", ".csv", ".json", ".log", ".pdf")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate()
    init_db()      # tables / extension / index
    get_model()    # Load the embedding model at startup to avoid delaying the first request.
    yield


app = FastAPI(title="RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    query: str = Field(max_length=4000)
    document_id: int | None = None  # Optional: restrict the search to a single file.


@app.get("/health")
def health():
    return {"status": "ok"}


# These synchronous endpoints run in FastAPI's thread pool, so blocking embedding
# and Groq calls do not block the server's event loop.


@app.post("/api/upload")
def upload(file: UploadFile = File(...)):
    filename = file.filename or "unknown"
    if len(filename) > 255:
        raise HTTPException(400, "The file name must not exceed 255 characters.")
    if not filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(400, f"Only these file types are allowed: {', '.join(ALLOWED_EXT)}")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"File exceeds the {settings.max_upload_mb} MB upload limit.")

    try:
        doc_id, n_chunks = ingest_document(filename, data)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"document_id": doc_id, "filename": filename, "chunks": n_chunks}


@app.post("/api/chat")
def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(400, "Query must not be empty.")

    # 1) Check the cache first; on a hit, skip both search and the Groq call.
    cache_version = cache.get_corpus_version()
    cached = cache.get_answer(query, req.document_id, cache_version)
    if cached is not None:
        return {**cached, "cached": True}

    contexts = search_chunks(query, document_id=req.document_id)
    if not contexts:
        # Do not cache this response because a file may be uploaded later.
        return {"answer": "Upload a document before asking a question.", "sources": []}

    try:
        answer = generate_answer(query, contexts)
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    result = {
        "answer": answer,
        "sources": [
            {"filename": c["filename"], "score": round(c["score"], 3)} for c in contexts
        ],
    }
    cache.set_answer(query, req.document_id, result, cache_version)
    return {**result, "cached": False}