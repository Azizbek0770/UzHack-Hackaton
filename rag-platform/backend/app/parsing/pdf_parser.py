from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber

from app.core.logger import get_logger
from app.core.text_normalization import TextNormalizer
from app.models.schemas import DocumentChunk, Metadata

try:
    import fitz  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    fitz = None

try:
    from paddleocr import PaddleOCR  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PaddleOCR = None


@dataclass
class PdfParserConfig:
    """Configuration for PDF parsing and OCR fallback."""

    low_text_threshold: int = 30
    ocr_language: str = "ru"
    ocr_language_mode: str = "auto"
    ocr_min_confidence: float = 0.5
    enable_ocr: bool = True


class PdfParser:
    """PDF parser that extracts text and applies OCR for low-text pages."""

    def __init__(self, config: Optional[PdfParserConfig] = None) -> None:
        self._config = config or PdfParserConfig()
        self._logger = get_logger("pdf_parser")
        self._normalizer = TextNormalizer()
        self._ocr_engines = self._init_ocr_engines()
        self._ocr_cache: Dict[Tuple[str, int, int, int], str] = {}

    def parse(self, file_path: Path, company: str) -> List[DocumentChunk]:
        """Parse a PDF file into document chunks."""

        chunks: List[DocumentChunk] = []
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                for index, page in enumerate(pdf.pages):
                    text = self._extract_page_text(file_path, index, page)
                    if not text.strip():
                        self._logger.warning(
                            "Empty extracted text for file=%s page=%s",
                            file_path.name,
                            index,
                        )
                        text = "No extractable text on this page."
                    metadata = Metadata(company=company, doc_type="pdf", file_name=file_path.name)
                    chunks.append(
                        DocumentChunk(content=text, page_index=index + 1, metadata=metadata)
                    )
        except Exception as exc:
            self._logger.error("PDF parsing failed for file=%s error=%s", file_path.name, exc)
            raise
        return chunks

    def _extract_page_text(self, file_path: Path, page_index: int, page: object) -> str:
        """Extract text from one page with fallback chain."""

        text = ""
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            self._logger.warning(
                "pdfplumber extraction failed for file=%s page=%s error=%s",
                file_path.name,
                page_index,
                exc,
            )
        if len(text.strip()) < self._config.low_text_threshold:
            fitz_text = self._extract_with_fitz_text(file_path, page_index)
            text = f"{text}\n{fitz_text}".strip()
        if self._should_ocr(text):
            ocr_text = self._run_ocr(file_path, page_index, text)
            text = f"{text}\n{ocr_text}".strip()
        return self._normalizer.normalize(text)

    def _should_ocr(self, text: str) -> bool:
        """Determine whether OCR is required for a page."""

        return self._config.enable_ocr and len(text.strip()) < self._config.low_text_threshold

    def _init_ocr_engines(self) -> Dict[str, PaddleOCR]:
        """Initialize OCR engine set if available."""

        if not self._config.enable_ocr:
            return {}
        if PaddleOCR is None:
            self._logger.warning("PaddleOCR is not installed; OCR disabled.")
            return {}
        languages = (
            ["ru", "en"]
            if self._config.ocr_language_mode == "auto"
            else [self._config.ocr_language]
        )
        engines: Dict[str, PaddleOCR] = {}
        for language in languages:
            try:
                engines[language] = PaddleOCR(lang=language)
            except Exception as exc:
                self._logger.warning("Failed to initialize OCR language %s: %s", language, exc)
        return engines

    def _run_ocr(self, file_path: Path, page_index: int, extracted_text: str) -> str:
        """Run OCR on a PDF page using PaddleOCR."""

        if not self._ocr_engines or fitz is None:
            return ""
        stats = file_path.stat()
        cache_key = (str(file_path.resolve()), page_index, int(stats.st_mtime), int(stats.st_size))
        cached = self._ocr_cache.get(cache_key)
        if cached is not None:
            return cached
        with fitz.open(str(file_path)) as document:
            page = document.load_page(page_index)
            pix = page.get_pixmap(dpi=220)
            image_bytes = pix.tobytes("png")
        language = self._select_ocr_language(extracted_text)
        engine = self._ocr_engines.get(language)
        if engine is None:
            engine = next(iter(self._ocr_engines.values()))
        result = engine.ocr(image_bytes, cls=True)
        text_lines: List[str] = []
        if result and result[0]:
            for item in result[0]:
                text_value = str(item[1][0])
                confidence = float(item[1][1])
                if confidence >= self._config.ocr_min_confidence:
                    text_lines.append(text_value)
        normalized = self._normalizer.normalize("\n".join(text_lines))
        self._ocr_cache[cache_key] = normalized
        return normalized

    @staticmethod
    def _extract_with_fitz_text(file_path: Path, page_index: int) -> str:
        """Fallback text extraction from PyMuPDF text layer."""

        if fitz is None:
            return ""
        try:
            with fitz.open(str(file_path)) as document:
                page = document.load_page(page_index)
                return page.get_text("text") or ""
        except Exception:
            return ""

    def _select_ocr_language(self, text: str) -> str:
        """Select OCR language from extracted content hints."""

        if self._config.ocr_language_mode != "auto":
            return self._config.ocr_language
        cyrillic_chars = sum(1 for char in text if "А" <= char <= "я")
        latin_chars = sum(1 for char in text if ("a" <= char.lower() <= "z"))
        if cyrillic_chars >= latin_chars:
            return "ru"
        return "en"
