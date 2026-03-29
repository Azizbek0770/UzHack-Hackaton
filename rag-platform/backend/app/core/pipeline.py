"""
RAG Pipeline Orchestrator
Coordinates all pipeline stages: ingestion → embedding → indexing → retrieval → QA.
Central control point for the entire system.
"""

from __future__ import annotations

import time
from typing import List, Optional, Union

import structlog

from app.core.config import settings
from app.core.ingestion import IngestionEngine
from app.core.logging import TimingLogger
from app.models.schemas import (
    ConfidenceLevel,
    DebugInfo,
    DocumentChunk,
    QueryRequest,
    QueryResponse,
    QueryType,
    SourceReference,
    TableChunk,
)
from app.qa.classifier import QueryAnalysis, QueryClassifier
from app.qa.llm_qa import LLMQAModule
from app.qa.table_qa import TableQAEngine
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.embeddings import EmbeddingEngine
from app.retrieval.faiss_index import IndexManager
from app.retrieval.hybrid import HybridRetriever
from app.utils.cache import QueryCache
from app.utils.confidence import compute_confidence

logger = structlog.get_logger(__name__)


class RAGPipeline:
    """
    Full RAG pipeline for financial document QA.

    Lifecycle:
    1. initialize() → load or build indexes
    2. query() → answer user questions
    3. shutdown() → cleanup resources
    """

    def __init__(self):
        self.embedder = EmbeddingEngine()
        self.index_manager = IndexManager()
        self.bm25 = BM25Retriever()
        self.retriever: Optional[HybridRetriever] = None
        self.classifier = QueryClassifier()
        self.table_qa = TableQAEngine()
        self.llm_qa = LLMQAModule()
        self.cache = QueryCache(
            enabled=settings.CACHE_ENABLED,
            max_size=settings.CACHE_MAX_SIZE,
            ttl_seconds=settings.CACHE_TTL_SECONDS,
        )
        self._all_chunks: List[Union[DocumentChunk, TableChunk]] = []

    async def initialize(self) -> None:
        """
        Initialize the pipeline.
        Loads indexes from disk if available, otherwise runs ingestion.
        """
        index_path = settings.INDEX_DIR

        # Try to load existing indexes
        loaded = self.index_manager.load(index_path) and self.bm25.load(index_path)

        if not loaded and settings.INGEST_ON_STARTUP:
            logger.info("No indexes found, running ingestion")
            await self._run_ingestion()
        elif loaded:
            logger.info(
                "Indexes loaded from disk",
                text_chunks=self.index_manager.text_index.size,
                table_chunks=self.index_manager.table_index.size,
                bm25_docs=self.bm25.size,
            )

        # Build the hybrid retriever
        self.retriever = HybridRetriever(
            index_manager=self.index_manager,
            bm25_retriever=self.bm25,
            embedding_engine=self.embedder,
        )

    async def _run_ingestion(self) -> None:
        """Full ingestion: parse → embed → index → persist."""
        engine = IngestionEngine()

        with TimingLogger("ingestion", logger):
            chunks, result = engine.ingest_all()

        if not chunks:
            logger.warning("No chunks produced from ingestion")
            return

        self._all_chunks = chunks
        logger.info("Ingestion complete", result=result.model_dump())

        # Embed all chunks
        with TimingLogger("embedding", logger, n=len(chunks)):
            chunks = self.embedder.embed_chunks(chunks)

        # Build FAISS indexes
        with TimingLogger("faiss_build", logger):
            self.index_manager.build_from_chunks(chunks)

        # Build BM25 index
        with TimingLogger("bm25_build", logger):
            self.bm25.build(chunks)

        # Persist to disk
        self.index_manager.save(settings.INDEX_DIR)
        self.bm25.save(settings.INDEX_DIR)

        logger.info(
            "Indexes built and saved",
            text_chunks=self.index_manager.text_index.size,
            table_chunks=self.index_manager.table_index.size,
        )

    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a user query through the full RAG pipeline.

        Pipeline stages:
        1. Cache check
        2. Query classification
        3. Hybrid retrieval
        4. Table QA attempt (programmatic)
        5. LLM QA (for complex reasoning)
        6. Response assembly
        """
        start = time.perf_counter()
        timings: dict = {}

        # 1. Cache check
        cached = self.cache.get(request.question)
        if cached:
            logger.debug("Cache hit", question=request.question[:60])
            return cached.response

        # 2. Query classification
        with TimingLogger("classify", logger) as t:
            analysis = self.classifier.analyze(request.question)
        timings["classify_ms"] = t.elapsed_ms

        # Override company filter if classifier found one
        company_filter = request.company_filter or analysis.target_company

        # 3. Retrieval
        if self.retriever is None:
            return self._error_response("Pipeline not initialized", start)

        with TimingLogger("retrieve", logger) as t:
            retrieved = self.retriever.retrieve(
                query=request.question,
                query_type=analysis.query_type,
                top_k=request.top_k,
                company_filter=company_filter,
                doc_type_filter=request.doc_type_filter.value if request.doc_type_filter else None,
            )
        timings["retrieve_ms"] = t.elapsed_ms

        chunks = [c for c, _ in retrieved]
        scores = [s for _, s in retrieved]

        if not chunks:
            return self._no_results_response(start, analysis.query_type)

        # 4. Table QA — try programmatic extraction first
        answer: Optional[str] = None
        confidence: float = 0.0
        qa_source = "llm"

        if analysis.query_type in (QueryType.TABLE, QueryType.NUMERIC):
            with TimingLogger("table_qa", logger) as t:
                table_result = self.table_qa.extract_answer(chunks, analysis, request.question)
            timings["table_qa_ms"] = t.elapsed_ms

            if table_result:
                answer, confidence, _ = table_result
                qa_source = "table"
                logger.info("Answer found via Table QA", confidence=confidence)

        # 5. LLM QA — if table QA didn't find answer or for textual queries
        if answer is None:
            with TimingLogger("llm_qa", logger) as t:
                answer, confidence = await self.llm_qa.answer(
                    request.question, chunks, analysis
                )
            timings["llm_qa_ms"] = t.elapsed_ms

        # 6. Confidence calibration
        final_confidence = compute_confidence(
            raw_confidence=confidence,
            retrieval_scores=scores,
            n_chunks=len(chunks),
            qa_source=qa_source,
        )

        # 7. Assemble response
        processing_ms = round((time.perf_counter() - start) * 1000, 2)
        sources = self._build_sources(chunks, include_excerpts=request.debug)

        debug_info = None
        if request.debug:
            debug_info = DebugInfo(
                query_type=analysis.query_type,
                rewritten_query=None,
                retrieved_text_chunks=sum(1 for c in chunks if isinstance(c, DocumentChunk)),
                retrieved_table_chunks=sum(1 for c in chunks if isinstance(c, TableChunk)),
                stage_timings=timings,
                top_chunks=[
                    {
                        "source": c.source_label,
                        "score": round(s, 4),
                        "type": c.chunk_type.value,
                        "excerpt": (c.content if isinstance(c, DocumentChunk) else c.summary)[:200],
                    }
                    for c, s in retrieved[:5]
                ],
            )

        response = QueryResponse(
            answer=answer,
            confidence=final_confidence,
            confidence_level=ConfidenceLevel.HIGH,  # will be overridden by validator
            query_type=analysis.query_type,
            processing_time_ms=processing_ms,
            relevant_chunks=sources,
            debug=debug_info,
        )

        # Cache the response
        self.cache.set(request.question, response)

        logger.info(
            "Query complete",
            ms=processing_ms,
            confidence=final_confidence,
            qa_source=qa_source,
            sources=len(sources),
        )
        return response

    def _build_sources(
        self,
        chunks: List[Union[DocumentChunk, TableChunk]],
        include_excerpts: bool = False,
    ) -> List[SourceReference]:
        """Convert chunks to SourceReference list, deduplicated by file+page."""
        seen = set()
        sources = []

        for chunk in chunks:
            page = chunk.page if isinstance(chunk, DocumentChunk) else None
            sheet = chunk.sheet_name if isinstance(chunk, TableChunk) else None
            key = f"{chunk.metadata.file_name}:{page}:{sheet}"

            if key in seen:
                continue
            seen.add(key)

            excerpt = None
            if include_excerpts:
                content = chunk.content if isinstance(chunk, DocumentChunk) else chunk.summary
                excerpt = content[:300]

            sources.append(SourceReference(
                file=chunk.metadata.file_name,
                page=page,
                sheet=sheet,
                company=chunk.metadata.company,
                doc_type=chunk.metadata.doc_type.value,
                chunk_type=chunk.chunk_type.value,
                excerpt=excerpt,
            ))

        return sources

    def _error_response(self, message: str, start: float) -> QueryResponse:
        return QueryResponse(
            answer=f"Ошибка системы: {message}",
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            query_type=QueryType.TEXTUAL,
            processing_time_ms=round((time.perf_counter() - start) * 1000, 2),
            relevant_chunks=[],
        )

    def _no_results_response(self, start: float, query_type: QueryType) -> QueryResponse:
        return QueryResponse(
            answer="Информация по данному запросу не найдена в предоставленных документах.",
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            query_type=query_type,
            processing_time_ms=round((time.perf_counter() - start) * 1000, 2),
            relevant_chunks=[],
        )

    async def shutdown(self) -> None:
        """Graceful shutdown — save any in-memory state."""
        logger.info("Pipeline shutdown complete")
