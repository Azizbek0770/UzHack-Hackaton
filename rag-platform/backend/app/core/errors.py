from __future__ import annotations


class DocumentProcessingError(RuntimeError):
    """Raised when a document cannot be processed."""


class RetrievalError(RuntimeError):
    """Raised when retrieval fails."""


class QAError(RuntimeError):
    """Raised when QA fails."""
