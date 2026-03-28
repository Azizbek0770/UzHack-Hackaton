from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.audit_db import AuditStore
from app.core.cache import InMemoryCache
from app.core.config import RetrievalSettings, get_settings
from app.core.telemetry import TelemetryCollector
from app.embeddings.embedder import EmbeddingModel
from app.qa.citation import CitationAssembler
from app.qa.llm import LLMClient
from app.qa.question_router import QuestionRouter
from app.qa.service import QAService
from app.retrieval.bm25_store import BM25Store
from app.retrieval.faiss_store import FaissStore
from app.retrieval.hybrid import HybridRetriever
from app.tables.table_qa import TableQAEngine


@lru_cache
def get_cache() -> InMemoryCache:
    """Return a shared cache instance."""

    settings = get_settings()
    return InMemoryCache(ttl_seconds=settings.cache_ttl_seconds)


@lru_cache
def get_embedder() -> EmbeddingModel:
    """Return the embedding model instance."""

    settings = get_settings()
    return EmbeddingModel(model_name=settings.embedding_model)


@lru_cache
def get_retriever() -> HybridRetriever:
    """Return the hybrid retriever instance."""

    embedder = get_embedder()
    text_store = FaissStore(embedder)
    table_store = FaissStore(embedder)
    bm25_store = BM25Store()
    settings = RetrievalSettings()
    retriever = HybridRetriever(
        text_store=text_store,
        table_store=table_store,
        bm25_store=bm25_store,
        settings=settings,
    )
    app_settings = get_settings()
    retriever.load(Path(app_settings.index_directory))
    return retriever


@lru_cache
def get_telemetry() -> TelemetryCollector:
    """Return shared telemetry collector."""

    settings = get_settings()
    return TelemetryCollector(window_size=settings.telemetry_window_size)


@lru_cache
def get_audit_store() -> AuditStore:
    """Return shared audit store."""

    settings = get_settings()
    return AuditStore(Path(settings.audit_db_file))


@lru_cache
def get_qa_service() -> QAService:
    """Return the QA service singleton."""

    retriever = get_retriever()
    table_qa = TableQAEngine()
    question_router = QuestionRouter()
    citation_assembler = CitationAssembler()
    telemetry = get_telemetry()
    settings = get_settings()
    llm_client = LLMClient(endpoint=settings.llm_endpoint, api_key=settings.llm_api_key)
    cache = get_cache()
    return QAService(
        retriever=retriever,
        table_qa=table_qa,
        llm_client=llm_client,
        cache=cache,
        question_router=question_router,
        citation_assembler=citation_assembler,
        telemetry=telemetry,
    )
