# RAG Document Chat Application

A full-stack Retrieval-Augmented Generation (RAG) application that lets users upload document files, convert them into searchable vector chunks, and ask questions about the uploaded content using a language model.

This project combines:
- A React + TypeScript frontend for the user experience
- A FastAPI backend for ingestion, retrieval, and chat APIs
- PostgreSQL with the pgvector extension for efficient vector similarity search
- FastEmbed for local embedding generation
- Groq for grounded LLM responses

## Project Overview

The application follows a standard RAG pipeline:

1. The user uploads a supported file.
2. The backend extracts readable text from the file.
3. The text is split into overlapping chunks.
4. Each chunk is converted into an embedding vector.
5. The embeddings are stored in PostgreSQL using pgvector.
6. When a question is asked, the query is embedded and matched against stored chunks.
7. Relevant chunks are retrieved and sent to the LLM as context.
8. The model generates a grounded answer based only on the retrieved context.

## Features

- File upload support for text and PDF files
- Document ingestion pipeline with chunking and vector storage
- Similarity search over stored embeddings
- Question answering grounded in uploaded documents
- Multi-stage UI flow: upload -> search -> chat
- FastAPI REST endpoints for backend integrations
- PostgreSQL + pgvector for vector indexing and retrieval
- Local embedding model execution via FastEmbed

## Tech Stack

### Frontend
- React 19
- TypeScript
- Vite
- Framer Motion

### Backend
- Python 3.14+
- FastAPI
- Uvicorn
- Psycopg
- pgvector
- FastEmbed
- Groq SDK
- PyPDF
- python-dotenv

### Database
- PostgreSQL 16
- pgvector extension

## Repository Structure

```text
rag/
├── client/                     # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat-screen.tsx
│   │   │   ├── file-uploader.tsx
│   │   │   ├── parent.tsx
│   │   │   └── searchbar.tsx
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
│
├── server/                    # FastAPI backend and app logic
│   ├── app/
│   │   ├── chunking.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── embed.py
│   │   ├── ingest.py
│   │   ├── llm.py
│   │   ├── main.py
│   │   └── search.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   ├── uv.lock
│   └── README.md
│
├── .gitignore
└── README.md                 # Project overview and setup guide
```

## High-Level Architecture

```mermaid
flowchart LR
    User --> Frontend
    Frontend -->|Upload document| API
    API --> Ingestion
    Ingestion --> Database
    Ingestion --> Embeddings
    Query --> API
    API --> Search
    Search --> Database
    Search --> LLM
    LLM --> Answer
    Answer --> Frontend
```

## Supported File Types

The backend currently allows these extensions:

- .txt
- .md
- .csv
- .json
- .log
- .pdf

Files are validated during upload and rejected if unsupported.

## Configuration

The backend reads environment variables from a `.env` file located in the `server` directory.

Example `.env`:

Create a local `.env` by copying the sample file in the `server` folder:

```bash
cp server/.env.example server/.env
```

Example `.env`:

```env
DATABASE_URL=postgresql://raguser:change_me_local_password@localhost:5433/ragdb
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
EMBED_MODEL=BAAI/bge-small-en-v1.5
EMBED_DIM=384
CHUNK_SIZE=800
CHUNK_OVERLAP=150
TOP_K=5
MAX_UPLOAD_MB=5
CORS_ORIGINS=http://localhost:5173

POSTGRES_USER=raguser
POSTGRES_PASSWORD=change_me_local_password
POSTGRES_DB=ragdb
```

Notes:
- `DATABASE_URL` should match your PostgreSQL configuration.
- `GROQ_API_KEY` is required for LLM answer generation.
- `EMBED_DIM` must match the selected embedding model.
- `CORS_ORIGINS` should include the frontend origin used by the React app.

## Setup Instructions

### 1. Clone the Project

```bash
git clone <repository-url>
cd rag
```

### 2. Set Up the Backend

From the `server` directory:

```bash
cd server
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or .venv\Scripts\activate  # Windows PowerShell

uv sync
```

If you are not using `uv`, install dependencies with:

```bash
pip install -e .
```

### 3. Start PostgreSQL

You can run the database with Docker Compose:

```bash
cd server
docker compose up -d db
```

This starts PostgreSQL with the pgvector extension installed.

### 4. Start the API Server

```bash
cd server
uvicorn app.main:app --reload
```

The API will be available at:
- http://127.0.0.1:8000
- Swagger Docs: http://127.0.0.1:8000/docs

### 5. Start the Frontend

Open a second terminal and run:

```bash
cd client
npm install
npm run dev
```

The frontend will run at:
- http://localhost:5173

## Running with Docker

The project includes a `docker-compose.yml` for the database and the API service. From the `server` directory:

```bash
cd server
docker compose up --build
```

This starts:
- PostgreSQL database with pgvector
- API container exposed on port 8000

## API Endpoints

### Health Check

```http
GET /health
```

Returns:

```json
{
  "status": "ok"
}
```

### Upload a Document

```http
POST /api/upload
```

Multipart-form upload:
- file: uploaded document

Response:

```json
{
  "document_id": 1,
  "filename": "example.pdf",
  "chunks": 12
}
```

### Ask a Question

```http
POST /api/chat
```

Request body:

```json
{
  "query": "What does the document say about project goals?",
  "document_id": 1
}
```

`document_id` is optional. If omitted, the system searches across all uploaded documents.

Response:

```json
{
  "answer": "The document states that the main goal is to improve ...",
  "sources": [
    {
      "filename": "example.pdf",
      "score": 0.87
    }
  ]
}
```

## Backend Components

### `app/config.py`
Defines application settings and loads environment variables.

### `app/db.py`
Initializes the PostgreSQL connection and creates the required vector tables and indexes.

### `app/embed.py`
Loads and reuses the embedding model, then converts text into vector representations.

### `app/chunking.py`
Splits large documents into smaller overlapping chunks for better retrieval quality.

### `app/ingest.py`
Extracts text from files, chunks it, embeds it, and stores the vectors in the database.

### `app/search.py`
Embeds the user query and performs similarity search in the vector database.

### `app/llm.py`
Sends retrieved chunks and the user question to Groq and returns the final answer.

### `app/main.py`
Contains the FastAPI application, upload endpoint, health endpoint, and chat endpoint.

## Frontend Flow

The frontend is a three-step guided flow:

1. Upload document
2. Search within the uploaded document or continue to chat
3. Ask questions and receive grounded answers

Key components:
- `FileUploader`: accepts file uploads and validates allowed extensions
- `SearchBar`: collects the user query
- `ChatScreen`: sends the question to the API and displays responses
- `parent.tsx`: manages the overall multi-stage flow

## Development Notes

- The backend is designed to preprocess and load the embedding model once at startup to reduce initial latency.
- `pgvector` is used for cosine similarity search, which is ideal for semantic retrieval.
- The app stores only the uploaded file name and text chunks, with embeddings kept in the vector database.
- The current implementation focuses on local embedding generation and retrieval quality rather than advanced caching or authentication.

## Future Enhancements

Possible improvements for this project include:

- Support for DOCX and HTML files
- Persistent user sessions and per-user document history
- Better chunking strategies for large structured documents
- Hybrid search with keyword + vector retrieval
- Reranking for improved relevance
- Authentication and authorization
- Dockerized full-stack startup for one-command developer setup
- Monitoring, logs, and evaluation metrics

## License

This project is currently provided as a local application codebase without a formal license declaration. If you plan to distribute or publish it, add an explicit license file and update this section accordingly.

## Conclusion

This project demonstrates a practical end-to-end document Q&A workflow using a modern RAG architecture. It is a good foundation for document search, knowledge retrieval, and AI-powered answer generation over uploaded content.
