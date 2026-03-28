from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Metadata(BaseModel):
    """Metadata for a company document."""

    company: str = Field(..., description="Company name extracted from dataset path.")
    doc_type: Literal["pdf", "xlsx", "json"] = Field(..., description="Document type.")
    file_name: str = Field(..., description="Source file name.")

    @field_validator("company", "file_name")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Metadata fields must not be empty.")
        return normalized


class DocumentChunk(BaseModel):
    """Textual chunk extracted from documents."""

    content: str = Field(..., description="Chunk content.")
    page_index: int = Field(..., description="Page index for PDFs or section index for JSON.")
    metadata: Metadata

    @field_validator("content")
    @classmethod
    def _content_not_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Document chunk content must not be empty.")
        return normalized


class TableChunk(BaseModel):
    """Tabular chunk extracted from spreadsheets."""

    content: dict[str, Any] = Field(..., description="Structured table JSON.")
    sheet_index: int = Field(..., description="Sheet index within the workbook.")
    metadata: Metadata

    @field_validator("content")
    @classmethod
    def _table_content_shape(cls, value: dict[str, Any]) -> dict[str, Any]:
        if "rows" not in value or "columns" not in value:
            raise ValueError("Table chunk content must include rows and columns.")
        return value


class SourceRef(BaseModel):
    """Reference to a document location for citations."""

    file: str
    page: int
    company: Optional[str] = None
    doc_type: Optional[Literal["pdf", "xlsx", "json"]] = None
    score: Optional[float] = None


class QueryRequest(BaseModel):
    """Input schema for question answering."""

    question: str
    company: Optional[str] = None
    doc_type: Optional[Literal["pdf", "xlsx", "json"]] = None


class QueryResponse(BaseModel):
    """Output schema for question answering."""

    answer: str
    relevant_chunks: list[SourceRef] = Field(default_factory=list)
    response_time_ms: Optional[int] = None
    query_mode: Optional[Literal["table", "text", "hybrid"]] = None
    answer_confidence: Optional[float] = None
    contradiction_warning: Optional[bool] = None
