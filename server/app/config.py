import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
_DATABASE_URL_VARIABLE = (
    "DATABASE_URL_PRODUCTION" if _APP_ENV == "production" else "DATABASE_URL_LOCAL"
)


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise RuntimeError(f"{name} must be either 'true' or 'false'.")
    return normalized == "true"


@dataclass(frozen=True)
class Settings:
    app_env: str = _APP_ENV

    # --- Database ---
    database_url: str = os.getenv(_DATABASE_URL_VARIABLE, "").strip()

    # --- Groq (LLM) ---
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = "openai/gpt-oss-120b"

    # --- Embeddings ---
    embed_model: str = "BAAI/bge-small-en-v1.5"
    embed_dim: int = 384

    # --- Chunking ---
    chunk_size: int = 800
    chunk_overlap: int = 150

    # --- Search ---
    top_k: int = 5

    # --- Upload ---
    max_upload_mb: int = 5

    # --- Cache (Redis) ---
    cache_enabled: bool = _read_bool("CACHE_ENABLED", False)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl_seconds: int = 3600

    # --- CORS ---
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )

    def validate(self) -> None:
        if self.app_env not in {"development", "production"}:
            raise RuntimeError("APP_ENV must be either 'development' or 'production'.")
        if not self.database_url:
            raise RuntimeError(f"{_DATABASE_URL_VARIABLE} must be configured.")
        if self.embed_dim <= 0:
            raise RuntimeError("Embedding dimension must be a positive integer.")
        if self.chunk_size <= 0 or not 0 <= self.chunk_overlap < self.chunk_size:
            raise RuntimeError(
                "Chunk overlap must be non-negative and smaller than chunk size."
            )
        if self.top_k <= 0 or self.max_upload_mb <= 0 or self.cache_ttl_seconds <= 0:
            raise RuntimeError(
                "Search, upload, and cache limits must be positive."
            )

        if self.app_env == "production":
            required = {
                "DATABASE_URL_PRODUCTION": self.database_url,
                "GROQ_API_KEY": self.groq_api_key,
                "CORS_ORIGINS": os.getenv("CORS_ORIGINS", ""),
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise RuntimeError(
                    "Missing required production environment variables: "
                    + ", ".join(missing)
                )
            database = urlsplit(self.database_url)
            if (
                database.scheme not in {"postgres", "postgresql"}
                or not database.hostname
                or database.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
            ):
                raise RuntimeError(
                    "DATABASE_URL_PRODUCTION must be a remote PostgreSQL URL."
                )
            if "*" in self.cors_origins or any(
                urlsplit(origin).scheme != "https" or not urlsplit(origin).hostname
                for origin in self.cors_origins
            ):
                raise RuntimeError(
                    "Production CORS_ORIGINS must contain only HTTPS origins."
                )
            if self.cache_enabled and not os.getenv("REDIS_URL", ""):
                raise RuntimeError("REDIS_URL is required when CACHE_ENABLED=true.")


settings = Settings()
