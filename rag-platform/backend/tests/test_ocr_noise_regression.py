from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.text_normalization import TextNormalizer


def test_text_normalizer_ru_ocr_noise_regression() -> None:
    """Normalizer keeps Russian semantics while cleaning OCR noise."""

    normalizer = TextNormalizer()
    raw = "Выручка   компании  1 200,5  млн  сум\n\n•••\nПрибыль-\nность выросла"
    cleaned = normalizer.normalize(raw)
    assert "Выручка компании 1 200,5 млн сум" in cleaned
    assert "Прибыльность выросла" in cleaned
    assert "•••" not in cleaned


def test_text_normalizer_uz_ocr_noise_regression() -> None:
    """Normalizer keeps Uzbek Latin text and removes duplicated noisy lines."""

    normalizer = TextNormalizer()
    raw = "Daromad 2024 yil 3000 mln so'm\nDaromad 2024 yil 3000 mln so'm\n\n▪▪▪\nFoyda  800"
    cleaned = normalizer.normalize(raw)
    assert cleaned.count("Daromad 2024 yil 3000 mln so'm") == 1
    assert "Foyda 800" in cleaned
    assert "▪▪▪" not in cleaned
