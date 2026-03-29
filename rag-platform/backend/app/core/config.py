"""
Application Configuration — Pydantic Settings
All configuration is driven by environment variables with sane defaults.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings.
    Override any field via environment variable (uppercase).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "RAG Financial Platform"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = True

    # ── Paths ─────────────────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATASET_DIR: Path = Field(default=None)
    INDEX_DIR: Path = Field(default=None)
    CACHE_DIR: Path = Field(default=None)

    @field_validator("DATASET_DIR", "INDEX_DIR", "CACHE_DIR", mode="before")
    @classmethod
    def resolve_dirs(cls, v, info):
        """Resolve relative paths against BASE_DIR."""
        base = Path(__file__).resolve().parent.parent.parent
        if v is None:
            name = info.field_name.replace("_DIR", "").lower()
            mapping = {"dataset": "dataset", "index": "indexes", "cache": ".cache"}
            return base / mapping.get(name, name)
        return Path(v)

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ── Embedding Model ───────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"  # "cuda" for GPU
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DIM: int = 1024  # bge-m3 output dim

    # ── FAISS ─────────────────────────────────────────────────────────────────
    FAISS_INDEX_TYPE: str = "IVFFlat"  # or "Flat" for small datasets
    FAISS_NLIST: int = 50             # number of Voronoi cells
    FAISS_NPROBE: int = 10            # cells to search at query time

    # ── Retrieval ─────────────────────────────────────────────────────────────
    RETRIEVAL_TOP_K: int = 10         # candidates from each retriever
    RETRIEVAL_FINAL_K: int = 5        # final chunks after reranking
    BM25_WEIGHT: float = 0.3          # weight for BM25 in hybrid fusion
    DENSE_WEIGHT: float = 0.7         # weight for dense retrieval

    # ── LLM ───────────────────────────────────────────────────────────────────
    LLM_PROVIDER: str = "openai"      # "openai" | "anthropic" | "ollama"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None  # for Ollama or custom endpoints
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.1      # low temp for factual QA

    # ── OCR ───────────────────────────────────────────────────────────────────
    OCR_ENABLED: bool = True
    OCR_LOW_TEXT_THRESHOLD: int = 50  # chars per page to trigger OCR
    OCR_LANG: str = "ru"              # PaddleOCR language

    # ── Chunking ──────────────────────────────────────────────────────────────
    CHUNK_MAX_TOKENS: int = 512
    CHUNK_OVERLAP_TOKENS: int = 64
    CHUNK_MIN_CHARS: int = 50         # discard chunks smaller than this

    # ── Cache ─────────────────────────────────────────────────────────────────
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600     # 1 hour
    CACHE_MAX_SIZE: int = 512         # max entries in LRU cache

    # ── Pipeline ──────────────────────────────────────────────────────────────
    PIPELINE_TIMEOUT_SECONDS: float = 30.0
    INGEST_ON_STARTUP: bool = True    # run ingestion if index missing


settings = Settings()

# Ensure runtime directories exist
for _dir in [settings.INDEX_DIR, settings.CACHE_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
