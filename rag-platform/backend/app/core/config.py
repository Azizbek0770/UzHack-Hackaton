from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORAGE_DIR = BACKEND_ROOT / "storage"


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "RAG Financial Platform"
    environment: str = "development"
    dataset_path: str = str(BACKEND_ROOT / "data")
    ocr_enabled: bool = True
    embedding_model: str = "BAAI/bge-m3"
    llm_endpoint: Optional[str] = None
    llm_api_key: Optional[str] = None
    cache_ttl_seconds: int = 300
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    ingest_on_startup: bool = True
    index_directory: str = str(DEFAULT_STORAGE_DIR / "indexes")
    ingestion_manifest_file: str = str(DEFAULT_STORAGE_DIR / "ingestion_manifest.json")
    ingestion_report_file: str = str(DEFAULT_STORAGE_DIR / "ingestion_report.json")
    audit_db_file: str = str(DEFAULT_STORAGE_DIR / "audit.sqlite3")
    controlled_dataset_path: str = str(DEFAULT_STORAGE_DIR / "real_dataset")
    enable_incremental_ingestion: bool = True
    ocr_language_mode: str = "auto"
    ocr_min_confidence: float = 0.5
    telemetry_window_size: int = 300

    model_config = SettingsConfigDict(env_prefix="RAG_")


class RetrievalSettings(BaseModel):
    """Configuration for retrieval and ranking."""

    text_top_k: int = 5
    table_top_k: int = 5
    bm25_weight: float = 0.4
    dense_weight: float = 0.6
    min_merged_score: float = 0.05


@lru_cache
def get_settings() -> AppSettings:
    """Return cached application settings."""

    return AppSettings()
