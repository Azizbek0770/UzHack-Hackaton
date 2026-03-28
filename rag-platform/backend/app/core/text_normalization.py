from __future__ import annotations

import re
import unicodedata


class TextNormalizer:
    """Normalize noisy multilingual text for stable downstream processing."""

    _space_pattern = re.compile(r"[ \t\f\v]+")
    _line_space_pattern = re.compile(r"[ \t]+\n")
    _many_newlines_pattern = re.compile(r"\n{3,}")
    _ocr_noise_pattern = re.compile(r"[•·●▪◦]+")
    _broken_hyphen_pattern = re.compile(r"(\w)-\n(\w)")

    def normalize(self, text: str) -> str:
        """Normalize encoding, whitespace, and common OCR artifacts."""

        if not text:
            return ""
        value = unicodedata.normalize("NFKC", text)
        value = value.replace("\r\n", "\n").replace("\r", "\n")
        value = self._broken_hyphen_pattern.sub(r"\1\2", value)
        value = self._ocr_noise_pattern.sub(" ", value)
        value = self._space_pattern.sub(" ", value)
        value = self._line_space_pattern.sub("\n", value)
        value = self._many_newlines_pattern.sub("\n\n", value)
        lines = [self._clean_line(line) for line in value.split("\n")]
        compacted = self._deduplicate_adjacent_lines(lines)
        return "\n".join(compacted).strip()

    @staticmethod
    def _clean_line(line: str) -> str:
        cleaned = line.strip()
        cleaned = re.sub(r"[|]{3,}", "||", cleaned)
        cleaned = re.sub(r"_{3,}", "__", cleaned)
        return cleaned

    @staticmethod
    def _deduplicate_adjacent_lines(lines: list[str]) -> list[str]:
        output: list[str] = []
        previous = None
        for line in lines:
            if not line and (previous is None or previous == ""):
                continue
            if previous is not None and line == previous and len(line) > 8:
                continue
            output.append(line)
            previous = line
        return output
