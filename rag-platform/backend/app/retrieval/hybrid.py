"""
Hybrid Retrieval System
Combines dense (FAISS) + sparse (BM25) retrieval via Reciprocal Rank Fusion.
Includes query rewriting for improved recall.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import structlog

from app.core.config import settings
from app.core.logging import TimingLogger
from app.models.schemas import DocumentChunk, QueryType, TableChunk
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.faiss_index import IndexManager

logger = structlog.get_logger(__name__)

RetrievalResult = List[Tuple[Union[DocumentChunk, TableChunk], float]]


class HybridRetriever:
    """
    Hybrid retrieval fusing dense and sparse signals.

    Uses Reciprocal Rank Fusion (RRF) to combine ranked lists,
    which is more robust than linear score combination when
    scores from different retrievers have different distributions.

    RRF formula: score = Σ 1/(k + rank_i) for each retriever i
    where k=60 is a smoothing constant.
    """

    RRF_K = 60  # standard RRF smoothing constant

    def __init__(
        self,
        index_manager: IndexManager,
        bm25_retriever: BM25Retriever,
        embedding_engine,  # EmbeddingEngine (avoid circular import)
    ):
        self.index_manager = index_manager
        self.bm25 = bm25_retriever
        self.embedder = embedding_engine

    def retrieve(
        self,
        query: str,
        query_type: QueryType,
        top_k: int = settings.RETRIEVAL_FINAL_K,
        company_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> RetrievalResult:
        """
        Full hybrid retrieval pipeline.

        Steps:
        1. Optionally rewrite query for better retrieval
        2. Dense search (FAISS) on text index
        3. Dense search (FAISS) on table index (if query might be table-based)
        4. BM25 search
        5. RRF fusion
        6. Return top_k

        Args:
            query: User question.
            query_type: Classified query type.
            top_k: Final number of chunks to return.
            company_filter: Optional company restriction.
            doc_type_filter: Optional doc type restriction.
        """
        fetch_k = settings.RETRIEVAL_TOP_K
        rewritten = self._rewrite_query(query, query_type)

        logger.debug(
            "Hybrid retrieval",
            original=query[:80],
            rewritten=rewritten[:80] if rewritten != query else "[no rewrite]",
            query_type=query_type.value,
        )

        all_results: List[RetrievalResult] = []
        filters = {
            "company_filter": company_filter,
            "doc_type_filter": doc_type_filter,
        }

        # 1. Dense: text index
        with TimingLogger("dense_text", logger):
            query_vec = self.embedder.embed_query(rewritten)
            text_results = self.index_manager.search_text(query_vec, fetch_k, **filters)
            if text_results:
                all_results.append(text_results)

        # 2. Dense: table index (always include for financial queries)
        with TimingLogger("dense_table", logger):
            table_results = self.index_manager.search_table(query_vec, fetch_k, **filters)
            if table_results:
                all_results.append(table_results)

        # 3. BM25 sparse retrieval
        with TimingLogger("bm25", logger):
            bm25_results = self.bm25.search(rewritten, fetch_k, **filters)
            if bm25_results:
                all_results.append(bm25_results)

        # 4. RRF fusion
        fused = self._reciprocal_rank_fusion(all_results)

        # 5. Deduplicate by chunk_id
        seen_ids = set()
        deduped: RetrievalResult = []
        for chunk, score in fused:
            cid = chunk.chunk_id
            if cid not in seen_ids:
                seen_ids.add(cid)
                deduped.append((chunk, score))

        logger.debug(
            "Retrieval complete",
            dense_text=len(text_results),
            dense_table=len(table_results),
            bm25=len(bm25_results),
            fused=len(deduped),
            returning=min(top_k, len(deduped)),
        )

        return deduped[:top_k]

    def _reciprocal_rank_fusion(
        self, ranked_lists: List[RetrievalResult]
    ) -> RetrievalResult:
        """
        Merge multiple ranked lists using Reciprocal Rank Fusion.
        Returns a merged list sorted by RRF score descending.
        """
        chunk_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Union[DocumentChunk, TableChunk]] = {}

        for ranked_list in ranked_lists:
            for rank, (chunk, _original_score) in enumerate(ranked_list):
                cid = chunk.chunk_id
                rrf_score = 1.0 / (self.RRF_K + rank + 1)
                chunk_scores[cid] = chunk_scores.get(cid, 0.0) + rrf_score
                chunk_map[cid] = chunk

        sorted_ids = sorted(chunk_scores.keys(), key=lambda x: chunk_scores[x], reverse=True)
        return [(chunk_map[cid], chunk_scores[cid]) for cid in sorted_ids]

    def _rewrite_query(self, query: str, query_type: QueryType) -> str:
        """
        Lightweight rule-based query rewriting to improve retrieval.

        Adds financial context and expands abbreviations.
        For a production system, this could call an LLM for HyDE.
        """
        rewrites = {
            # Russian → expand common abbreviations
            "выручка": "выручка от реализации доходы от продаж revenue",
            "активы": "суммарные активы total assets баланс",
            "прибыль": "чистая прибыль net profit доходы",
            "убыток": "чистый убыток net loss",
            "капитал": "собственный капитал shareholders equity",
            # Uzbek
            "daromad": "daromad tushum выручка revenue",
            "foyda": "sof foyda net profit чистая прибыль",
        }

        enhanced = query
        lower = query.lower()
        for term, expansion in rewrites.items():
            if term in lower:
                enhanced = f"{query} {expansion}"
                break

        return enhanced
