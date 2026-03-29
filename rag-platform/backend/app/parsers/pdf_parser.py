"""
PDF Parser — PyMuPDF + PaddleOCR Fallback
Handles scanned PDFs, mixed-language content, and financial tables.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import structlog

from app.core.config import settings
from app.models.schemas import (
    ChunkType,
    DocType,
    DocumentChunk,
    DocumentMetadata,
    Language,
)
from app.parsers.base import BaseParser
from app.utils.language import detect_language
from app.utils.text import clean_text, is_meaningful

logger = structlog.get_logger(__name__)


class PDFParser(BaseParser):
    """
    Parses PDF files into DocumentChunk objects.

    Strategy:
    1. Extract text with PyMuPDF (fast, preserves layout)
    2. If a page has < OCR_LOW_TEXT_THRESHOLD chars → apply PaddleOCR
    3. Semantic chunk per page (pages are natural document sections)
    4. Tag each chunk with source metadata
    """

    def __init__(self):
        self._ocr_engine = None  # lazy-loaded

    def _load_ocr(self):
        """Lazy-load PaddleOCR to avoid startup overhead."""
        if self._ocr_engine is None and settings.OCR_ENABLED:
            try:
                from paddleocr import PaddleOCR
                self._ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=settings.OCR_LANG,
                    show_log=False,
                )
                logger.info("PaddleOCR engine loaded")
            except ImportError:
                logger.warning(
                    "PaddleOCR not installed. OCR fallback disabled. "
                    "Install with: pip install paddlepaddle paddleocr"
                )
        return self._ocr_engine

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"

    def parse(self, file_path: Path, metadata: DocumentMetadata) -> List[DocumentChunk]:
        """
        Parse a PDF file into a list of DocumentChunks.

        Args:
            file_path: Path to the PDF file.
            metadata: Pre-populated document metadata.

        Returns:
            List of DocumentChunk objects, one or more per page.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise RuntimeError("PyMuPDF not installed. Run: pip install pymupdf")

        chunks: List[DocumentChunk] = []

        try:
            doc = fitz.open(str(file_path))
            metadata.total_pages = len(doc)
            logger.info(
                "Parsing PDF",
                file=file_path.name,
                pages=len(doc),
                company=metadata.company,
            )

            for page_num, page in enumerate(doc, start=1):
                text = self._extract_page_text(page, page_num, file_path)

                if not is_meaningful(text, min_chars=settings.CHUNK_MIN_CHARS):
                    logger.debug("Skipping empty page", page=page_num)
                    continue

                # Detect language from first substantial page
                if metadata.language == Language.UNKNOWN and len(text) > 200:
                    metadata.language = detect_language(text)

                # Create one chunk per page (pages = natural section boundaries)
                chunk = DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    content=clean_text(text),
                    chunk_type=ChunkType.TEXT,
                    metadata=metadata.model_copy(),
                    page=page_num,
                    section=self._extract_section_heading(text),
                )
                chunks.append(chunk)

            doc.close()

        except Exception as e:
            logger.error("PDF parsing failed", file=str(file_path), error=str(e))
            raise

        logger.info(
            "PDF parsed successfully",
            file=file_path.name,
            chunks=len(chunks),
        )
        return chunks

    def _extract_page_text(
        self, page, page_num: int, file_path: Path
    ) -> str:
        """
        Extract text from a single PDF page.
        Falls back to OCR if the extracted text is below the threshold.
        """
        # Primary: PyMuPDF text extraction
        text = page.get_text("text")

        if len(text.strip()) >= settings.OCR_LOW_TEXT_THRESHOLD:
            return text

        # Fallback: OCR
        logger.debug(
            "Low text on page, attempting OCR",
            page=page_num,
            chars=len(text.strip()),
        )
        ocr_text = self._ocr_page(page, file_path, page_num)
        return ocr_text if ocr_text else text

    def _ocr_page(self, page, file_path: Path, page_num: int) -> Optional[str]:
        """
        Run PaddleOCR on a rendered page image.
        Returns extracted text or None if OCR unavailable/failed.
        """
        engine = self._load_ocr()
        if engine is None:
            return None

        try:
            # Render page to image at 2x resolution for better OCR accuracy
            mat = page.get_pixmap(matrix=__import__("fitz").Matrix(2, 2))
            img_bytes = mat.tobytes("png")

            import numpy as np
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(img_bytes))
            img_array = np.array(img)

            result = engine.ocr(img_array, cls=True)
            if not result or not result[0]:
                return None

            lines = [line[1][0] for line in result[0] if line[1][1] > 0.5]
            return "\n".join(lines)

        except Exception as e:
            logger.warning("OCR failed for page", page=page_num, error=str(e))
            return None

    def _extract_section_heading(self, text: str) -> Optional[str]:
        """
        Heuristically extract a section heading from page text.
        Looks for short all-caps lines or lines matching common financial patterns.
        """
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return None

        for line in lines[:5]:  # check first 5 lines
            # All-caps heading (common in Russian financial docs)
            if len(line) > 5 and line == line.upper() and not line[0].isdigit():
                return line[:100]
            # Numbered section (e.g. "1. Общие сведения")
            if re.match(r"^\d+[\.\)]\s+\w", line):
                return line[:100]

        return lines[0][:100] if lines else None
