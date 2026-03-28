from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.parsing.json_parser import JsonParser
from app.parsing.pdf_parser import PdfParser, PdfParserConfig
from app.parsing.xlsx_parser import XlsxParser


class FakePage:
    """Fake PDF page for testing."""

    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        """Return extracted text."""

        return self._text


class FakePdf:
    """Fake PDF container for testing."""

    def __init__(self, pages: list[FakePage]) -> None:
        self.pages = pages

    def __enter__(self) -> "FakePdf":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


def test_json_parser(tmp_path: Path) -> None:
    """Parse JSON into a document chunk."""

    file_path = tmp_path / "company.json"
    file_path.write_text('{"name": "Acme"}', encoding="utf-8")
    parser = JsonParser()
    chunks = parser.parse(file_path, "Acme")
    assert len(chunks) == 1
    assert "Acme" in chunks[0].content


def test_xlsx_parser(tmp_path: Path) -> None:
    """Parse XLSX into table chunks."""

    file_path = tmp_path / "report.xlsx"
    df = pd.DataFrame({"Metric": ["Revenue"], "Value": [100]})
    df.to_excel(file_path, index=False)
    parser = XlsxParser()
    chunks = parser.parse(file_path, "Acme")
    assert len(chunks) == 1
    assert chunks[0].content["rows"][0]["Metric"] == "Revenue"


def test_pdf_parser_text_only(monkeypatch) -> None:
    """Parse PDF with text extraction."""

    def fake_open(path: str) -> FakePdf:
        return FakePdf([FakePage("Sample text")])

    monkeypatch.setattr("pdfplumber.open", fake_open)
    parser = PdfParser(PdfParserConfig(enable_ocr=False))
    chunks = parser.parse(Path("sample.pdf"), "Acme")
    assert len(chunks) == 1
    assert "Sample text" in chunks[0].content


def test_pdf_parser_empty_page_has_fallback_text(monkeypatch) -> None:
    """Ensure empty page extraction still yields stable non-empty chunk content."""

    def fake_open(path: str) -> FakePdf:
        return FakePdf([FakePage("")])

    monkeypatch.setattr("pdfplumber.open", fake_open)
    parser = PdfParser(PdfParserConfig(enable_ocr=False))
    chunks = parser.parse(Path("sample.pdf"), "Acme")
    assert len(chunks) == 1
    assert chunks[0].content
