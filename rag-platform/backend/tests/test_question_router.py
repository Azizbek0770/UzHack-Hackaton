from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.qa.question_router import QuestionRouter


def test_question_router_detects_table_mode() -> None:
    """Router identifies financial metric question as table mode."""

    router = QuestionRouter()
    analysis = router.analyze("What is revenue in 2024?")
    assert analysis.mode == "table"
    assert analysis.detected_year == "2024"
    assert analysis.has_numeric_intent


def test_question_router_detects_text_mode() -> None:
    """Router identifies narrative question as text mode."""

    router = QuestionRouter()
    analysis = router.analyze("What are the strategic risks mentioned by management?")
    assert analysis.mode == "text"
    assert not analysis.has_table_intent
