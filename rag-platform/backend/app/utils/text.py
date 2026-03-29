"""
Text Utilities — cleaning, validation, normalization.
"""

from __future__ import annotations

import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean extracted text for storage and embedding.
    - Normalize unicode
    - Collapse whitespace
    - Remove control characters
    - Preserve Cyrillic, Latin, digits, punctuation
    """
    # Normalize unicode (NFC)
    text = unicodedata.normalize("NFC", text)

    # Remove control characters (except newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)

    # Collapse multiple spaces (but preserve newlines for structure)
    text = re.sub(r"[^\S\n]+", " ", text)

    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def is_meaningful(text: str, min_chars: int = 50) -> bool:
    """
    Check if a text chunk is meaningful enough to index.
    Filters out page numbers, headers with only numbers, etc.
    """
    if not text or len(text.strip()) < min_chars:
        return False

    stripped = text.strip()

    # Only digits or punctuation
    if re.match(r"^[\d\s\.\,\-\/\\]+$", stripped):
        return False

    # Too few words
    words = [w for w in stripped.split() if len(w) > 1]
    if len(words) < 5:
        return False

    return True


def truncate(text: str, max_chars: int = 500, suffix: str = "...") -> str:
    """Truncate text to max_chars, appending suffix if truncated."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)].rstrip() + suffix


def extract_numbers(text: str) -> list[float]:
    """Extract all numeric values from a text string."""
    pattern = r"[-+]?\d[\d\s]*(?:[.,]\d+)?"
    matches = re.findall(pattern, text)
    results = []
    for m in matches:
        try:
            normalized = m.replace(" ", "").replace(",", ".")
            results.append(float(normalized))
        except ValueError:
            continue
    return results
