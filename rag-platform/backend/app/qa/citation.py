from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.models.schemas import SourceRef


@dataclass
class CitationResult:
    """Output of citation assembly for final answer."""

    answer: str
    confidence: float
    contradiction_warning: bool


class CitationAssembler:
    """Build sentence-level citation markers and confidence estimate."""

    def assemble(self, answer: str, sources: Iterable[SourceRef], context: str) -> CitationResult:
        """Attach source markers to answer and evaluate consistency."""

        source_list = list(sources)
        if not source_list:
            return CitationResult(
                answer=answer.strip(),
                confidence=0.0,
                contradiction_warning=False,
            )
        sentences = self._split_sentences(answer)
        marked_sentences: list[str] = []
        for index, sentence in enumerate(sentences, start=1):
            marker = min(index, len(source_list))
            marked_sentences.append(f"{sentence.strip()} [S{marker}]")
        confidence = self._estimate_confidence(answer, source_list, context)
        contradiction_warning = self._detect_contradiction(answer, context)
        return CitationResult(
            answer=" ".join(marked_sentences).strip(),
            confidence=confidence,
            contradiction_warning=contradiction_warning,
        )

    @staticmethod
    def _split_sentences(answer: str) -> list[str]:
        parts = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", answer.strip()) if segment.strip()]
        if parts:
            return parts
        return [answer.strip()]

    @staticmethod
    def _estimate_confidence(answer: str, sources: list[SourceRef], context: str) -> float:
        answer_tokens = set(re.findall(r"[a-zA-Zа-яА-Я0-9]+", answer.lower()))
        context_tokens = set(re.findall(r"[a-zA-Zа-яА-Я0-9]+", context.lower()))
        if not answer_tokens:
            return 0.0
        overlap = len(answer_tokens & context_tokens) / len(answer_tokens)
        source_weight = min(1.0, len(sources) / 4.0)
        score = (overlap * 0.7) + (source_weight * 0.3)
        return round(max(0.0, min(1.0, score)), 4)

    @staticmethod
    def _detect_contradiction(answer: str, context: str) -> bool:
        answer_numbers = set(re.findall(r"-?\d+(?:[.,]\d+)?", answer))
        if not answer_numbers:
            return False
        context_numbers = set(re.findall(r"-?\d+(?:[.,]\d+)?", context))
        return not answer_numbers.issubset(context_numbers)
