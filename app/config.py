# config.py - Application configuration and settings
# Loads all environment variables in one place so nothing is hardcoded elsewhere.

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Google Gemini ──────────────────────────────────────────────────────────
    GOOGLE_API_KEY: str

    # Model names (google-genai SDK identifiers)
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    CHAT_MODEL: str = "gemini-2.5-flash"

    # ── Vector store ──────────────────────────────────────────────────────────
    VECTOR_DB_PATH: str = "./data/chroma_db"

    # ── Text splitting ────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # ── Retrieval ─────────────────────────────────────────────────────────────
    TOP_K_RESULTS: int = 4

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (reads .env once)."""
    return Settings()
