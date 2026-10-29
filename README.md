# RAG Document Chat

A full-stack Retrieval-Augmented Generation application for uploading text documents and PDFs, searching their contents, and asking questions grounded in the uploaded material.

## Architecture

- **Frontend:** React, TypeScript, and Vite (`client/`)
- **API:** FastAPI and FastEmbed (`server/`)
- **Database:** PostgreSQL with the `pgvector` extension
- **Answer generation:** Groq
- **Optional cache:** Redis

The API stores document text chunks and embeddings in PostgreSQL. Uploaded files are processed in memory and are not retained as files. The embedding model is downloaded when the API starts.

Retrieved document chunks and the question are sent to Groq to generate each answer. Documents remain in PostgreSQL until removed directly from the database; the application does not currently provide a document deletion endpoint. Confirm that your data-handling requirements permit this storage and third-party processing before uploading sensitive documents.

## Security notice

The API does not require authentication. Anyone who can reach the deployed API can upload documents and query the shared corpus. Do not deploy it publicly or upload sensitive documents unless access is restricted by a trusted platform-level access control layer. Per-user accounts, document ownership, and authorization are not implemented.

## Environment variables

Use one root `.env` file for local development. Copy the example once if you do not already have `.env`:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Set your Groq API key in the root `.env` before asking questions.

### Local `.env` variables

| Variable | Development | Production |
|---|---|---|
| `DATABASE_URL_LOCAL` | Local PostgreSQL URL on `localhost:5433` | Not used |
| `DATABASE_URL_PRODUCTION` | Leave empty | Set in the Render API service to the PostgreSQL provider's private connection URL |
| `APP_ENV` | `development` | `production` (the Docker image defaults to production; Docker Compose sets development) |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Local Docker Compose database credentials | Not used |
| `GROQ_API_KEY` | Your development Groq key | Your production Groq key |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Set in the frontend build environment to the API's public HTTPS URL |
| `CACHE_ENABLED` | `true` for local Redis; set `false` to disable caching | Set in the Render API service; use `true` only with Redis |
| `REDIS_URL` | `redis://localhost:6379/0` | Set in the Render API service to a private Redis URL when caching is enabled |

The backend and Vite both load the root `.env`. Docker Compose reads it with `--env-file`, requires local PostgreSQL credentials from it, and constructs a container-only URL. The backend selects `DATABASE_URL_LOCAL` in development and `DATABASE_URL_PRODUCTION` only when `APP_ENV=production`. The Docker image defaults to production; Docker Compose explicitly sets development for local use. Production will fail startup if its URL is missing or points to a local database. No production URL is currently present in this repository's local environment file. Set the actual existing production database URL in Render's API service as a secret; do not point production at the development database. The application never creates, migrates, or deletes the managed database resource itself, but initializes its tables on startup.

The following stable settings are defaults in `server/app/config.py` and do not need `.env` entries: `GROQ_MODEL`, `EMBED_MODEL`, `EMBED_DIM`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `MAX_UPLOAD_MB`, and `CACHE_TTL_SECONDS`. For Render, confirm `APP_ENV=production` (the Docker image already defaults to this) and set `CORS_ORIGINS` to the exact HTTPS frontend origin.

### Frontend variable

Set `VITE_API_BASE_URL=http://localhost:8000` in the root `.env` for development. In production, set it to the API's public HTTPS URL in the frontend service's **build environment**, then rebuild/redeploy the frontend. `VITE_` variables are public and embedded in the built JavaScript: never put credentials or secrets in them.

`PORT` is assigned by the hosting platform. The Docker entry point uses it automatically; do not set it manually.

## Local development

Requirements: Python 3.14+, `uv`, Node.js, npm, and Docker.

1. Copy the environment templates and set `GROQ_API_KEY`.
2. Start the database and Redis from the repository root:

   ```powershell
   Set-Location server
   docker compose --env-file ..\\.env up -d db redis
   ```

3. In a backend terminal:

   ```powershell
   Set-Location server
   uv sync
   uv run uvicorn app.main:app --reload
   ```

4. In a frontend terminal:

   ```powershell
   Set-Location client
   npm ci
   npm run dev
   ```

The frontend is served at `http://localhost:5173` and the API at `http://localhost:8000`. The API initializes its tables on startup; the PostgreSQL instance must have `pgvector` available.

To run the backend and local dependencies in containers instead:

```powershell
Set-Location server
docker compose --env-file ..\\.env up --build
```

## Deploying to Render

Deploy separate API and frontend services, plus a PostgreSQL database:

1. **API:** create a Docker web service with `server` as its **Root Directory** and `Dockerfile` as its **Dockerfile Path** (relative to that root). This makes the build context contain `pyproject.toml`, `uv.lock`, and `app/`, which the Dockerfile copies. Do not leave the root directory at the repository root or set the Dockerfile path to `server/Dockerfile` while the root is already `server`. Configure `/health` as the health-check path. The image listens on Render's assigned `PORT`.
2. **Database:** use the existing production PostgreSQL database and set its private connection URL as `DATABASE_URL_PRODUCTION` in the API service. Confirm the database supports `pgvector` and allows the application to create or use the `vector` extension. Extension availability and permissions depend on the database provider; the API cannot start successfully without it.
3. **API environment:** set `APP_ENV=production`, `DATABASE_URL_PRODUCTION` to the existing production database's private PostgreSQL URL, `GROQ_API_KEY`, and `CORS_ORIGINS`. Set `CORS_ORIGINS` to the exact HTTPS origin of the deployed frontend, such as `https://your-site.onrender.com`. Mark credentials as secret values. Production database connections require TLS. For optional Redis, configure a production Redis service, set its private URL in `REDIS_URL`, and set `CACHE_ENABLED=true`; otherwise set `CACHE_ENABLED=false`.
4. **Frontend:** create a static site with `client` as its root directory, `npm ci && npm run build` as its build command, and `dist` as its publish directory. Set `VITE_API_BASE_URL` to the API's public HTTPS URL in the frontend build environment and deploy again whenever that URL changes.
5. Before deployment, configure a trusted access-control layer for the API, or restrict access to a private network. The application itself does not authenticate users.

Production startup validates required settings, a remote PostgreSQL URL, HTTPS CORS origins, and invalid chunking or limit values. Render's local filesystem is ephemeral; documents and vectors are persisted in PostgreSQL, but the embedding model may be downloaded again after an instance restart. Select an instance with enough memory for FastEmbed.

## API

- `GET /health` — public platform health check.
- `POST /api/upload` — uploads a `.txt`, `.md`, `.csv`, `.json`, `.log`, or `.pdf` file.
- `POST /api/chat` — answers a question using the shared document corpus. An optional `document_id` narrows the search.

Chat requests accept JSON such as:

```json
{
  "query": "What does the document say about project goals?",
  "document_id": 1
}
```

## Validation

Run the frontend type-check/build and lint from `client/`:

```powershell
npm run build
npm run lint
```

Check the Python sources from `server/`:

```powershell
uv run python -m compileall app
```
