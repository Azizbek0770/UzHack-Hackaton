"""
FastAPI Route Definitions
All API endpoints for the RAG platform.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.pipeline import RAGPipeline
from app.models.schemas import IngestionResult, QueryRequest, QueryResponse

logger = structlog.get_logger(__name__)
router = APIRouter()


# ── Dependency: get pipeline from app state ───────────────────────────────────

def get_pipeline(request: Request) -> RAGPipeline:
    """FastAPI dependency to retrieve the RAG pipeline from app state."""
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline not initialized. Check server logs.",
        )
    return pipeline


# ── Query Endpoint ────────────────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query financial documents",
    description=(
        "Submit a question about company financials. "
        "The system retrieves relevant document chunks and generates a grounded answer."
    ),
    tags=["QA"],
)
async def query(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> QueryResponse:
    """
    Main QA endpoint.

    - Classifies the query type (numeric, textual, table)
    - Performs hybrid retrieval (FAISS + BM25)
    - Attempts programmatic table extraction
    - Falls back to LLM reasoning
    - Returns answer with source citations and confidence
    """
    try:
        response = await asyncio.wait_for(
            pipeline.query(request),
            timeout=settings.PIPELINE_TIMEOUT_SECONDS,
        )
        return response

    except asyncio.TimeoutError:
        logger.error("Query timed out", question=request.question[:60])
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Query timed out after {settings.PIPELINE_TIMEOUT_SECONDS}s",
        )
    except Exception as e:
        logger.error("Query failed", error=str(e), question=request.question[:60])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {type(e).__name__}",
        )


# ── Ingestion Endpoint ────────────────────────────────────────────────────────

@router.post(
    "/ingest",
    response_model=IngestionResult,
    summary="Trigger document ingestion",
    description="Re-runs the full ingestion pipeline. Use after adding new documents.",
    tags=["Admin"],
)
async def trigger_ingestion(
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> IngestionResult:
    """Re-run full document ingestion."""
    try:
        await pipeline._run_ingestion()
        return IngestionResult(
            successful=pipeline.index_manager.text_index.size,
            total_text_chunks=pipeline.index_manager.text_index.size,
            total_table_chunks=pipeline.index_manager.table_index.size,
        )
    except Exception as e:
        logger.error("Ingestion failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ── Status Endpoint ───────────────────────────────────────────────────────────

@router.get(
    "/status",
    summary="Pipeline status",
    tags=["System"],
)
async def status_endpoint(
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> Dict[str, Any]:
    """Returns current pipeline status and index sizes."""
    return {
        "status": "ready",
        "indexes": {
            "text_chunks": pipeline.index_manager.text_index.size,
            "table_chunks": pipeline.index_manager.table_index.size,
            "bm25_docs": pipeline.bm25.size,
        },
        "cache": {
            "enabled": settings.CACHE_ENABLED,
            "size": pipeline.cache.size,
            "max_size": settings.CACHE_MAX_SIZE,
        },
        "config": {
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.LLM_MODEL,
            "llm_provider": settings.LLM_PROVIDER,
            "retrieval_top_k": settings.RETRIEVAL_TOP_K,
            "final_top_k": settings.RETRIEVAL_FINAL_K,
        },
    }


# ── Cache Management ──────────────────────────────────────────────────────────

@router.delete(
    "/cache",
    summary="Clear query cache",
    tags=["Admin"],
)
async def clear_cache(
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> Dict[str, str]:
    """Clear the in-memory query cache."""
    pipeline.cache.clear()
    return {"message": "Cache cleared"}
