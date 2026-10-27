import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment values from the .env file (expected at the project root)
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # --- Database ---
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://raguser:ragpass@localhost:5432/ragdb"
    )

    # --- Groq (LLM) ---
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    # --- Embeddings (fastembed runs locally on CPU; no API key is required) ---
    embed_model: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    # If you change the model, the embedding dimension must also match (bge-small = 384)
    embed_dim: int = int(os.getenv("EMBED_DIM", "384"))

    # --- Chunking ---
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))      # characters
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))  # characters

    # --- Search ---
    top_k: int = int(os.getenv("TOP_K", "5"))

    # --- Upload ---
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "5"))

    # --- CORS (URL of the React frontend) ---
    cors_origins: tuple = tuple(
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    )


settings = Settings()