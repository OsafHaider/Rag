from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import cache
from app.config import settings
from app.db import init_db
from app.embed import get_model
from app.ingest import ingest_document
from app.llm import generate_answer
from app.search import search_chunks

ALLOWED_EXT = (".txt", ".md", ".csv", ".json", ".log", ".pdf")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()      # tables / extension / index
    get_model()    # embedding model pehle hi load kar lo (pehli request slow na ho)
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
    document_id: int | None = None  # optional: sirf ek file mein search karne ke liye


@app.get("/health")
def health():
    return {"status": "ok"}


# Note: yeh endpoints `def` (sync) hain, FastAPI inhe threadpool mein chalata hai,
# is liye embedding / Groq ke blocking calls server ko block nahi karte.


@app.post("/api/upload")
def upload(file: UploadFile = File(...)):
    filename = file.filename or "unknown"
    if not filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(400, f"Sirf yeh file types allowed hain: {', '.join(ALLOWED_EXT)}")

    data = file.file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File {settings.max_upload_mb}MB se badi hai")

    try:
        doc_id, n_chunks = ingest_document(filename, data)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"document_id": doc_id, "filename": filename, "chunks": n_chunks}


@app.post("/api/chat")
def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(400, "Query khali hai")

    # 1) Pehle cache dekho: hit ho to search aur Groq dono skip
    cache_version = cache.get_corpus_version()
    cached = cache.get_answer(query, req.document_id, cache_version)
    if cached is not None:
        return {**cached, "cached": True}

    contexts = search_chunks(query, document_id=req.document_id)
    if not contexts:
        # yeh jawab cache nahi karte, kal file upload ho sakti hai
        return {"answer": "Pehle koi file upload karein, phir sawal poochein.", "sources": []}

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