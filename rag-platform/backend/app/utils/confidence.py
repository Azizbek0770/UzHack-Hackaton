"""
Confidence Scoring Logic
Calibrates final confidence from multiple signals.
"""

from __future__ import annotations

from typing import List

import structlog

logger = structlog.get_logger(__name__)


def compute_confidence(
    raw_confidence: float,
    retrieval_scores: List[float],
    n_chunks: int,
    qa_source: str,  # "table" | "llm"
) -> float:
    """
    Calibrate a final confidence score from multiple signals.

    Factors:
    - LLM-reported confidence (raw_confidence)
    - Top retrieval score (how well does the best chunk match?)
    - Number of relevant chunks (more = higher signal)
    - QA source (table extraction = more reliable)

    Returns a float in [0.0, 1.0].
    """
    if not retrieval_scores:
        return max(0.0, raw_confidence * 0.5)

    top_score = max(retrieval_scores)
    avg_score = sum(retrieval_scores) / len(retrieval_scores)

    # Retrieval quality signal (FAISS inner product, normalized → [0,1])
    retrieval_signal = min(1.0, (top_score * 0.7 + avg_score * 0.3))

    # Chunk count bonus (more chunks = more evidence)
    chunk_bonus = min(0.1, n_chunks * 0.02)

    # Source reliability (programmatic table extraction is more reliable)
    source_multiplier = 1.05 if qa_source == "table" else 1.0

    # Weighted combination
    combined = (
        raw_confidence * 0.45
        + retrieval_signal * 0.45
        + chunk_bonus
    ) * source_multiplier

    result = round(max(0.0, min(1.0, combined)), 3)
    logger.debug(
        "Confidence computed",
        raw=raw_confidence,
        retrieval=retrieval_signal,
        final=result,
    )
    return result
