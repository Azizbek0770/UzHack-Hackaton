"""
Test Suite — RAG Platform
Covers: parsing, text utilities, query classification, confidence scoring.
Run with: pytest tests/ -v
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Text Utilities ────────────────────────────────────────────────────────────

class TestTextUtils:
    def test_clean_text_collapses_whitespace(self):
        from app.utils.text import clean_text
        result = clean_text("Hello   World\n\n\n\nTest")
        assert "   " not in result
        assert result.count("\n") <= 2

    def test_clean_text_removes_control_chars(self):
        from app.utils.text import clean_text
        result = clean_text("Hello\x00\x01World")
        assert "\x00" not in result
        assert "\x01" not in result

    def test_is_meaningful_short_text(self):
        from app.utils.text import is_meaningful
        assert not is_meaningful("Hi", min_chars=50)

    def test_is_meaningful_numeric_only(self):
        from app.utils.text import is_meaningful
        assert not is_meaningful("1234 5678 90", min_chars=5)

    def test_is_meaningful_valid_text(self):
        from app.utils.text import is_meaningful
        assert is_meaningful(
            "Выручка компании за 2023 год составила 1 234 млн рублей.",
            min_chars=20,
        )

    def test_extract_numbers(self):
        from app.utils.text import extract_numbers
        nums = extract_numbers("Выручка: 1 234,5 млн, прибыль: 42.0")
        assert len(nums) >= 1


# ── Language Detection ────────────────────────────────────────────────────────

class TestLanguageDetection:
    def test_detects_russian(self):
        from app.utils.language import detect_language
        from app.models.schemas import Language
        result = detect_language(
            "Финансовая отчётность компании за отчётный период."
        )
        assert result == Language.RUSSIAN

    def test_detects_english(self):
        from app.utils.language import detect_language
        from app.models.schemas import Language
        result = detect_language(
            "The company reported strong financial results for the year."
        )
        assert result == Language.ENGLISH

    def test_unknown_for_empty(self):
        from app.utils.language import detect_language
        from app.models.schemas import Language
        result = detect_language("")
        assert result == Language.UNKNOWN


# ── Query Classifier ─────────────────────────────────────────────────────────

class TestQueryClassifier:
    def setup_method(self):
        from app.qa.classifier import QueryClassifier
        self.clf = QueryClassifier()

    def test_classifies_numeric_query(self):
        from app.models.schemas import QueryType
        result = self.clf.analyze("Сколько составила выручка компании в 2023 году?")
        assert result.query_type in (QueryType.NUMERIC, QueryType.TABLE)
        assert result.target_metric == "revenue"
        assert result.target_year == 2023

    def test_classifies_textual_query(self):
        from app.models.schemas import QueryType
        result = self.clf.analyze("Кто является директором компании?")
        assert result.query_type == QueryType.TEXTUAL

    def test_classifies_table_query(self):
        from app.models.schemas import QueryType
        result = self.clf.analyze("Покажите финансовые показатели за 2022 год")
        assert result.query_type == QueryType.TABLE

    def test_extracts_year(self):
        result = self.clf.analyze("Каков объём активов в 2021 году?")
        assert result.target_year == 2021

    def test_extracts_metric(self):
        result = self.clf.analyze("Какова чистая прибыль?")
        assert result.target_metric == "profit"

    def test_multi_hop_detection(self):
        from app.models.schemas import QueryType
        result = self.clf.analyze(
            "Как изменилась выручка по сравнению с предыдущим годом?"
        )
        assert result.query_type == QueryType.MULTI_HOP


# ── JSON Parser ───────────────────────────────────────────────────────────────

class TestJSONParser:
    def test_parses_simple_json(self):
        from app.parsers.base import JSONParser
        from app.models.schemas import DocumentMetadata, DocType, Language

        parser = JSONParser()
        meta = DocumentMetadata(
            company="TestCo",
            file_name="meta.json",
            file_path="/tmp/meta.json",
            doc_type=DocType.METADATA,
            language=Language.UNKNOWN,
        )

        data = {"company": "TestCo", "founded": 2005, "employees": 1200}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp_path = Path(f.name)

        chunks = parser.parse(tmp_path, meta)
        assert len(chunks) == 1
        assert "TestCo" in chunks[0].content
        tmp_path.unlink()

    def test_returns_empty_for_invalid_json(self):
        from app.parsers.base import JSONParser
        from app.models.schemas import DocumentMetadata, DocType, Language

        parser = JSONParser()
        meta = DocumentMetadata(
            company="TestCo",
            file_name="bad.json",
            file_path="/tmp/bad.json",
            doc_type=DocType.METADATA,
            language=Language.UNKNOWN,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("NOT VALID JSON {{{")
            tmp_path = Path(f.name)

        chunks = parser.parse(tmp_path, meta)
        assert chunks == []
        tmp_path.unlink()


# ── Confidence Scoring ────────────────────────────────────────────────────────

class TestConfidenceScoring:
    def test_high_confidence_with_good_retrieval(self):
        from app.utils.confidence import compute_confidence
        score = compute_confidence(
            raw_confidence=0.9,
            retrieval_scores=[0.95, 0.88, 0.75],
            n_chunks=5,
            qa_source="table",
        )
        assert score >= 0.75

    def test_low_confidence_with_poor_retrieval(self):
        from app.utils.confidence import compute_confidence
        score = compute_confidence(
            raw_confidence=0.3,
            retrieval_scores=[0.2, 0.15],
            n_chunks=2,
            qa_source="llm",
        )
        assert score < 0.5

    def test_clamps_to_valid_range(self):
        from app.utils.confidence import compute_confidence
        score = compute_confidence(
            raw_confidence=2.0,  # Invalid — should clamp
            retrieval_scores=[1.5],
            n_chunks=10,
            qa_source="table",
        )
        assert 0.0 <= score <= 1.0

    def test_handles_empty_retrieval_scores(self):
        from app.utils.confidence import compute_confidence
        score = compute_confidence(
            raw_confidence=0.7,
            retrieval_scores=[],
            n_chunks=0,
            qa_source="llm",
        )
        assert 0.0 <= score <= 1.0


# ── Cache ─────────────────────────────────────────────────────────────────────

class TestQueryCache:
    def setup_method(self):
        from app.utils.cache import QueryCache
        self.cache = QueryCache(enabled=True, max_size=3, ttl_seconds=60)

    def _make_response(self, answer: str):
        from app.models.schemas import QueryResponse, QueryType, ConfidenceLevel
        return QueryResponse(
            answer=answer,
            confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            query_type=QueryType.TEXTUAL,
            processing_time_ms=100.0,
            relevant_chunks=[],
        )

    def test_set_and_get(self):
        r = self._make_response("Test answer")
        self.cache.set("What is revenue?", r)
        cached = self.cache.get("What is revenue?")
        assert cached is not None
        assert cached.response.answer == "Test answer"

    def test_case_insensitive_key(self):
        r = self._make_response("Answer")
        self.cache.set("What is revenue?", r)
        assert self.cache.get("WHAT IS REVENUE?") is not None

    def test_cache_miss(self):
        result = self.cache.get("nonexistent question xyz")
        assert result is None

    def test_lru_eviction(self):
        for i in range(4):
            self.cache.set(f"question {i}", self._make_response(f"answer {i}"))
        # Cache holds max 3 → first entry should be evicted
        assert self.cache.size <= 3

    def test_clear(self):
        self.cache.set("q", self._make_response("a"))
        self.cache.clear()
        assert self.cache.size == 0
