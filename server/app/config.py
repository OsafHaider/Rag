import os
from dataclasses import dataclass

from dotenv import load_dotenv

# .env file se values load karta hai (project root mein honi chahiye)
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # --- Database ---
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://raguser:ragpass@localhost:5433/ragdb"
    )

    # --- Groq (LLM) ---
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- Embeddings (fastembed, local CPU par chalta hai, API key nahi chahiye) ---
    embed_model: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    # Model badlein to dimension bhi match karna zaroori hai (bge-small = 384)
    embed_dim: int = int(os.getenv("EMBED_DIM", "384"))

    # --- Chunking ---
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))      # characters
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))  # characters

    # --- Search ---
    top_k: int = int(os.getenv("TOP_K", "5"))

    # --- Upload ---
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "5"))

    # --- Cache (Redis) ---
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # --- CORS (React frontend ka URL) ---
    cors_origins: tuple = tuple(
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    )


settings = Settings()