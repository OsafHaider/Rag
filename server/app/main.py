from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.db import init_db
from app.embed import get_model
from app.ingest import ingest_document
from app.llm import generate_answer
from app.search import search_chunks

ALLOWED_EXT = (".txt", ".md", ".csv", ".json", ".log", ".pdf")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()      # create tables / extension / indexes if needed
    get_model()    # preload the embedding model so the first request is not slow
    yield


app = FastAPI(title="RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    document_id: int | None = None  # optional: restrict the search to a single file


@app.get("/health")
def health():
    return {"status": "ok"}


# Note: these endpoints use `def` (sync) handlers, and FastAPI runs them in the threadpool.
# As a result, blocking embedding or Groq calls do not block the server.


@app.post("/api/upload")
def upload(file: UploadFile = File(...)):
    filename = file.filename or "unknown"
    if not filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(400, f"Only these file types are allowed: {', '.join(ALLOWED_EXT)}")

    data = file.file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb}MB")

    try:
        doc_id, n_chunks = ingest_document(filename, data)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"document_id": doc_id, "filename": filename, "chunks": n_chunks}


@app.post("/api/chat")
def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(400, "Query is empty")

    contexts = search_chunks(query, document_id=req.document_id)
    if not contexts:
        return {"answer": "Upload a file first, then ask a question.", "sources": []}

    try:
        answer = generate_answer(query, contexts)
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    return {
        "answer": answer,
        "sources": [
            {"filename": c["filename"], "score": round(c["score"], 3)} for c in contexts
        ],
    }