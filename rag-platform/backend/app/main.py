"""
RAG Platform - Main FastAPI Application Entry Point
Production-grade financial document QA system.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.pipeline import RAGPipeline
from app.core.logging import configure_logging

# Configure structured logging before anything else
configure_logging(debug=settings.DEBUG)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    Initializes and tears down the RAG pipeline on startup/shutdown.
    """
    logger.info("Starting RAG Platform", version=settings.VERSION, env=settings.ENV)

    # Initialize pipeline and attach to app state
    pipeline = RAGPipeline()
    try:
        await pipeline.initialize()
        app.state.pipeline = pipeline
        logger.info("RAG Pipeline initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize RAG pipeline", error=str(e))
        # Allow app to start even if pipeline init fails (for health checks)
        app.state.pipeline = None

    yield

    # Shutdown
    logger.info("Shutting down RAG Platform")
    if app.state.pipeline:
        await app.state.pipeline.shutdown()


def create_app() -> FastAPI:
    """
    Application factory — creates and configures the FastAPI app.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="Production-grade RAG system for financial document QA",
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request ID & timing middleware ────────────────────────────────────────
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Bind request context to logger
        with structlog.contextvars.bound_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        ):
            response = await call_next(request)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time-Ms"] = str(elapsed_ms)
            logger.debug("Request completed", status=response.status_code, ms=elapsed_ms)
            return response

    # ── Global error handler ──────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["system"])
    async def health_check():
        pipeline_ready = hasattr(app.state, "pipeline") and app.state.pipeline is not None
        return {
            "status": "ok" if pipeline_ready else "degraded",
            "pipeline_ready": pipeline_ready,
            "version": settings.VERSION,
        }

    return app


app = create_app()
