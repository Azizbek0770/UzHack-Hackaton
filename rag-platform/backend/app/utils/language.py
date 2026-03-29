"""
Language Detection Utility
Detects Russian vs Uzbek vs English based on character frequency heuristics.
Avoids heavy dependencies like langdetect for speed.
"""

from __future__ import annotations

import re

from app.models.schemas import Language


# Uzbek-specific Latin characters not in Russian
UZBEK_LATIN_PATTERNS = re.compile(r"[oʻgʻ]|sh|ch|ng|[a-z]{3,}", re.IGNORECASE)

# Cyrillic character range
CYRILLIC = re.compile(r"[\u0400-\u04FF]")

# Uzbek Cyrillic-specific letters
UZBEK_CYRILLIC = re.compile(r"[ўқғҳ]", re.IGNORECASE)

# Russian-specific Cyrillic
RUSSIAN_CYRILLIC = re.compile(r"[ёъы]", re.IGNORECASE)


def detect_language(text: str) -> Language:
    """
    Heuristically detect the primary language of a text fragment.

    Strategy:
    1. Count Cyrillic characters
    2. If mostly Latin → check for Uzbek Latin patterns
    3. If Cyrillic → distinguish Russian vs Uzbek Cyrillic
    4. Default to UNKNOWN

    Args:
        text: Input text (first 500 chars recommended for speed)

    Returns:
        Language enum value
    """
    sample = text[:500]
    total = max(len(sample), 1)

    cyrillic_count = len(CYRILLIC.findall(sample))
    cyrillic_ratio = cyrillic_count / total

    # Mostly Latin script
    if cyrillic_ratio < 0.1:
        if UZBEK_LATIN_PATTERNS.search(sample):
            return Language.UZBEK
        # Check for common English words
        if re.search(r"\b(the|and|of|in|is|are|was|for)\b", sample, re.IGNORECASE):
            return Language.ENGLISH
        return Language.UNKNOWN

    # Mixed or Cyrillic-dominant
    uzbek_cyr = len(UZBEK_CYRILLIC.findall(sample))
    russian_cyr = len(RUSSIAN_CYRILLIC.findall(sample))

    if uzbek_cyr > russian_cyr:
        return Language.UZBEK
    if russian_cyr > 0 or cyrillic_ratio > 0.3:
        return Language.RUSSIAN

    return Language.UNKNOWN
