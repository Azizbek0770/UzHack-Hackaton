"""
Domain Models — Pydantic v2
Strongly typed data contracts for the entire RAG pipeline.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Enumerations ──────────────────────────────────────────────────────────────

class DocType(str, Enum):
    """Supported document types in the financial dataset."""
    FINANCIAL_REPORT = "financial_report"
    ANNUAL_REPORT = "annual_report"
    DISCLOSURE = "disclosure"
    METADATA = "metadata"
    UNKNOWN = "unknown"


class Language(str, Enum):
    """Supported content languages."""
    RUSSIAN = "ru"
    UZBEK = "uz"
    ENGLISH = "en"
    UNKNOWN = "unknown"


class ChunkType(str, Enum):
    """Whether a chunk originates from prose text or a structured table."""
    TEXT = "text"
    TABLE = "table"


class QueryType(str, Enum):
    """Classifier output — determines QA routing strategy."""
    NUMERIC = "numeric"       # e.g. "What was revenue in 2023?"
    TEXTUAL = "textual"       # e.g. "Who is the CEO?"
    TABLE = "table"           # e.g. "Show assets by year"
    MULTI_HOP = "multi_hop"   # requires chaining multiple facts


class ConfidenceLevel(str, Enum):
    HIGH = "high"       # > 0.75
    MEDIUM = "medium"   # 0.45 – 0.75
    LOW = "low"         # < 0.45


# ── Document Models ───────────────────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    """
    Metadata attached to every parsed document.
    Extracted from folder structure and file headers.
    """
    company: str = Field(..., description="Company identifier from folder name")
    file_name: str = Field(..., description="Original file name")
    file_path: str = Field(..., description="Absolute path to source file")
    doc_type: DocType = DocType.UNKNOWN
    language: Language = Language.UNKNOWN
    year: Optional[int] = Field(None, description="Fiscal year if detectable")
    total_pages: Optional[int] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    extra: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("year", mode="before")
    @classmethod
    def coerce_year(cls, v):
        if v is not None:
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return v


class DocumentChunk(BaseModel):
    """
    A text chunk from a document, ready for embedding and retrieval.
    Every field is populated — no optional source fields.
    """
    chunk_id: str = Field(..., description="Unique chunk identifier (uuid)")
    content: str = Field(..., min_length=1)
    chunk_type: ChunkType = ChunkType.TEXT
    metadata: DocumentMetadata

    # Source location within the document
    page: Optional[int] = Field(None, description="1-indexed page number (PDF)")
    section: Optional[str] = Field(None, description="Section heading if detectable")

    # Populated after embedding
    embedding: Optional[List[float]] = Field(None, exclude=True)

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        return v.strip()

    @property
    def source_label(self) -> str:
        """Human-readable source string for UI display."""
        loc = f"p.{self.page}" if self.page else ""
        return f"{self.metadata.file_name} {loc}".strip()


class TableChunk(BaseModel):
    """
    A structured table chunk from XLSX or PDF tables.
    Preserves the raw table data alongside a text summary for embedding.
    """
    chunk_id: str
    summary: str = Field(..., description="LLM-ready text summary of the table")
    raw_data: List[Dict[str, Any]] = Field(
        ..., description="List of row dicts from pandas"
    )
    headers: List[str]
    sheet_name: Optional[str] = None
    sheet_index: Optional[int] = None
    metadata: DocumentMetadata
    chunk_type: ChunkType = ChunkType.TABLE

    # Populated after embedding
    embedding: Optional[List[float]] = Field(None, exclude=True)

    @property
    def source_label(self) -> str:
        loc = f"sheet:{self.sheet_name}" if self.sheet_name else ""
        return f"{self.metadata.file_name} {loc}".strip()


# ── API Request / Response Models ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Incoming user query."""
    question: str = Field(..., min_length=3, max_length=2000)
    company_filter: Optional[str] = Field(
        None, description="Restrict retrieval to a specific company"
    )
    doc_type_filter: Optional[DocType] = Field(
        None, description="Restrict to a specific document type"
    )
    debug: bool = Field(False, description="Include retrieved chunks in response")
    top_k: int = Field(5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def clean_question(cls, v: str) -> str:
        return v.strip()


class SourceReference(BaseModel):
    """A single source reference returned with the answer."""
    file: str
    page: Optional[int] = None
    sheet: Optional[str] = None
    company: str
    doc_type: str
    chunk_type: str
    excerpt: Optional[str] = Field(
        None, description="Short excerpt from the chunk (debug / expandable view)"
    )


class DebugInfo(BaseModel):
    """Debug payload included when debug=True."""
    query_type: QueryType
    rewritten_query: Optional[str] = None
    retrieved_text_chunks: int = 0
    retrieved_table_chunks: int = 0
    stage_timings: Dict[str, float] = Field(default_factory=dict)
    top_chunks: List[Dict[str, Any]] = Field(default_factory=list)


class QueryResponse(BaseModel):
    """Full API response for a /query call."""
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    query_type: QueryType
    processing_time_ms: float
    relevant_chunks: List[SourceReference]
    debug: Optional[DebugInfo] = None

    @model_validator(mode="after")
    def set_confidence_level(self) -> "QueryResponse":
        if self.confidence >= 0.75:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.confidence >= 0.45:
            self.confidence_level = ConfidenceLevel.MEDIUM
        else:
            self.confidence_level = ConfidenceLevel.LOW
        return self


# ── Ingestion Models ──────────────────────────────────────────────────────────

class IngestionResult(BaseModel):
    """Summary of a document ingestion run."""
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    total_text_chunks: int = 0
    total_table_chunks: int = 0
    errors: List[Dict[str, str]] = Field(default_factory=list)
    duration_seconds: float = 0.0


# ── Cache Models ──────────────────────────────────────────────────────────────

class CachedResponse(BaseModel):
    """Wrapper for cached query responses."""
    response: QueryResponse
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    hit_count: int = 1
