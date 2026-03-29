"""
Pytest configuration and shared fixtures.
"""
import sys
from pathlib import Path

# Ensure the backend root is on the Python path so imports resolve correctly
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_client():
    """Create a test client with a mock pipeline."""
    from unittest.mock import AsyncMock, MagicMock
    from app.main import app

    # Mock the pipeline so tests don't need real indexes
    mock_pipeline = MagicMock()
    mock_pipeline.query = AsyncMock()
    app.state.pipeline = mock_pipeline

    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_document_metadata():
    from app.models.schemas import DocumentMetadata, DocType, Language
    return DocumentMetadata(
        company="TestBank",
        file_name="report_2023.pdf",
        file_path="/dataset/TestBank/report_2023.pdf",
        doc_type=DocType.FINANCIAL_REPORT,
        language=Language.RUSSIAN,
        year=2023,
    )
