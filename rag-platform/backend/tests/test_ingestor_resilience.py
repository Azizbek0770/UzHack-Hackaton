from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.ingestion.ingestor import DocumentIngestor
from app.models.schemas import DocumentChunk, Metadata


class IdentityChunker:
    def chunk(self, documents):
        return list(documents)


class DummyRetriever:
    def __init__(self) -> None:
        self.text = []
        self.tables = []

    def add_text_chunks(self, chunks):
        self.text.extend(chunks)

    def add_table_chunks(self, chunks):
        self.tables.extend(chunks)


class GoodJsonParser:
    def parse(self, file_path: Path, company: str):
        metadata = Metadata(company=company, doc_type="json", file_name=file_path.name)
        return [DocumentChunk(content="Valid payload", page_index=0, metadata=metadata)]


class FailingPdfParser:
    def parse(self, file_path: Path, company: str):
        raise RuntimeError("broken pdf")


def test_ingestor_continues_on_single_file_failure(tmp_path: Path) -> None:
    """Ingestor records failed file but keeps successful chunks."""

    company_dir = tmp_path / "Acme"
    company_dir.mkdir(parents=True)
    (company_dir / "good.json").write_text('{"ok": true}', encoding="utf-8")
    (company_dir / "bad.pdf").write_text("not a real pdf", encoding="utf-8")

    retriever = DummyRetriever()
    ingestor = DocumentIngestor(
        chunker=IdentityChunker(),
        retriever=retriever,
        pdf_parser=FailingPdfParser(),
        json_parser=GoodJsonParser(),
        incremental=False,
    )

    result = ingestor.ingest(tmp_path)
    assert result.processed_files == 1
    assert len(result.failed_files) == 1
    assert len(result.text_chunks) == 1
    assert result.pipeline_report.failed_files == 1
    assert any(file_item.error for file_item in result.pipeline_report.files)
