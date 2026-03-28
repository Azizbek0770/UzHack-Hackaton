from __future__ import annotations

import time
from typing import List, Optional, Union

from app.core.cache import InMemoryCache
from app.core.telemetry import QueryMetric, TelemetryCollector
from app.models.schemas import DocumentChunk, QueryResponse, SourceRef, TableChunk
from app.qa.citation import CitationAssembler
from app.qa.llm import LLMClient
from app.qa.question_router import QuestionRouter
from app.retrieval.hybrid import HybridRetriever
from app.tables.table_qa import TableQAEngine

ChunkType = Union[DocumentChunk, TableChunk]


class QAService:
    """Orchestrates retrieval, table QA, and LLM reasoning."""

    def __init__(
        self,
        retriever: HybridRetriever,
        table_qa: TableQAEngine,
        llm_client: LLMClient,
        cache: InMemoryCache,
        question_router: QuestionRouter,
        citation_assembler: CitationAssembler,
        telemetry: TelemetryCollector,
    ) -> None:
        self._retriever = retriever
        self._table_qa = table_qa
        self._llm_client = llm_client
        self._cache = cache
        self._question_router = question_router
        self._citation_assembler = citation_assembler
        self._telemetry = telemetry

    def answer(
        self,
        question: str,
        company: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> QueryResponse:
        """Answer a user question with source citations."""

        cache_key = f"{question}|{company}|{doc_type}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        start = time.time()
        question_analysis = self._question_router.analyze(question)
        retrieved = self._retriever.retrieve(
            question,
            mode=question_analysis.mode,
            company=company,
            doc_type=doc_type,
        )
        if not retrieved:
            latency = int((time.time() - start) * 1000)
            response = QueryResponse(
                answer="Insufficient context to answer from provided documents.",
                relevant_chunks=[],
                response_time_ms=latency,
                query_mode=question_analysis.mode,
                answer_confidence=0.0,
                contradiction_warning=False,
            )
            self._telemetry.add(
                QueryMetric(
                    latency_ms=latency,
                    retrieved_count=0,
                    source_count=0,
                    confidence=0.0,
                    mode=question_analysis.mode,
                )
            )
            self._cache.set(cache_key, response)
            return response
        table_chunks = [chunk for chunk, _ in retrieved if isinstance(chunk, TableChunk)][:8]
        text_chunks = [chunk for chunk, _ in retrieved if isinstance(chunk, DocumentChunk)][:8]
        table_answer = (
            self._table_qa.answer(question, table_chunks)
            if table_chunks and question_analysis.has_table_intent
            else None
        )
        if table_answer:
            latency = int((time.time() - start) * 1000)
            response = QueryResponse(
                answer=table_answer.answer,
                relevant_chunks=table_answer.sources,
                response_time_ms=latency,
                query_mode=question_analysis.mode,
                answer_confidence=0.95,
                contradiction_warning=False,
            )
            self._telemetry.add(
                QueryMetric(
                    latency_ms=latency,
                    retrieved_count=len(retrieved),
                    source_count=len(table_answer.sources),
                    confidence=0.95,
                    mode=question_analysis.mode,
                )
            )
            self._cache.set(cache_key, response)
            return response
        context = self._build_context(text_chunks, table_chunks)
        if not context:
            latency = int((time.time() - start) * 1000)
            response = QueryResponse(
                answer="Insufficient context to answer from provided documents.",
                relevant_chunks=[],
                response_time_ms=latency,
                query_mode=question_analysis.mode,
                answer_confidence=0.0,
                contradiction_warning=False,
            )
            self._telemetry.add(
                QueryMetric(
                    latency_ms=latency,
                    retrieved_count=len(retrieved),
                    source_count=0,
                    confidence=0.0,
                    mode=question_analysis.mode,
                )
            )
            self._cache.set(cache_key, response)
            return response
        llm_response = self._llm_client.answer(question, context)
        answer_text = llm_response.answer.strip() or self._extractive_fallback(context)
        sources = self._build_sources(retrieved)
        citation_result = self._citation_assembler.assemble(answer_text, sources, context)
        latency = int((time.time() - start) * 1000)
        response = QueryResponse(
            answer=citation_result.answer,
            relevant_chunks=sources,
            response_time_ms=latency,
            query_mode=question_analysis.mode,
            answer_confidence=citation_result.confidence,
            contradiction_warning=citation_result.contradiction_warning,
        )
        self._telemetry.add(
            QueryMetric(
                latency_ms=latency,
                retrieved_count=len(retrieved),
                source_count=len(sources),
                confidence=citation_result.confidence,
                mode=question_analysis.mode,
            )
        )
        self._cache.set(cache_key, response)
        return response

    @staticmethod
    def _build_context(
        text_chunks: List[DocumentChunk], table_chunks: List[TableChunk]
    ) -> str:
        """Build LLM context from retrieved chunks."""

        text_context = "\n\n".join(chunk.content for chunk in text_chunks[:5])
        table_context = "\n\n".join(
            str(chunk.content) for chunk in table_chunks[:2]
        )
        return "\n\n".join([text_context, table_context]).strip()

    @staticmethod
    def _build_sources(results: List[tuple[ChunkType, float]]) -> List[SourceRef]:
        """Convert chunks into source references."""

        sources: List[SourceRef] = []
        seen: set[str] = set()
        for chunk, score in results:
            page = chunk.page_index if isinstance(chunk, DocumentChunk) else chunk.sheet_index
            key = f"{chunk.metadata.file_name}:{page}:{chunk.metadata.company}"
            if key in seen:
                continue
            seen.add(key)
            sources.append(
                SourceRef(
                    file=chunk.metadata.file_name,
                    page=page,
                    company=chunk.metadata.company,
                    doc_type=chunk.metadata.doc_type,
                    score=round(score, 4),
                )
            )
            if len(sources) >= 8:
                break
        return sources

    @staticmethod
    def _extractive_fallback(context: str) -> str:
        """Return deterministic fallback answer from context when LLM output is empty."""

        lines = [line.strip() for line in context.splitlines() if line.strip()]
        if not lines:
            return "Insufficient context to answer from provided documents."
        return " ".join(lines[:3])
