# SikhSituationBot Test Configuration

import os
import pytest
import tempfile
from unittest.mock import MagicMock

# Test configuration
@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "database_url": "sqlite:///tests/fixtures/test_database.db",
        "gemini_api_key": "test-key",
        "test_data_path": "tests/fixtures/sample_shabads.json"
    }

@pytest.fixture(scope="session")
def sample_shabad_data():
    """Sample shabad data for testing."""
    return {
        "shabad_id": "test-1",
        "gurmukhi": "ਤਪਤਿ ਮਾਹਿ ਠਾਢਿ ਵਰਤਾਈ ॥",
        "romanization": "tapat maahi thaadh varataaee ||",
        "english_translation": "In the midst of the burning heat, a cooling breeze has begun to blow.",
        "context_tags": ["anxiety", "peace", "calm"],
        "source": "SGGS Page 1",
        "recommended_persona": "any"
    }

@pytest.fixture(scope="session")
def mock_gemini_response():
    """Mock Gemini API response."""
    return {
        "text": "This is a compassionate response about finding peace through Gurbani wisdom."
    }

@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary database for testing."""
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope="function")
def mock_genai():
    """Mock Google Generative AI."""
    with pytest.mock.patch('google.generativeai') as mock_genai:
        # Configure mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Mocked Gemini response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = MagicMock()

        yield mock_genai

@pytest.fixture(scope="function")
def mock_sentence_transformers():
    """Mock sentence transformers."""
    with pytest.mock.patch('sentence_transformers.SentenceTransformer') as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3] * 256]  # 768-dim vector
        mock_st.return_value = mock_model

        yield mock_st

# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "api: API-related tests")

def pytest_sessionstart(session):
    """Provide app context during test session."""
    try:
        from server.app import app
        session.app_ctx = app.app_context()
        session.app_ctx.push()
    except Exception as e:
        print(f"Warning: Could not push app context in sessionstart: {e}")

def pytest_sessionfinish(session, exitstatus):
    """Clean up app context."""
    if hasattr(session, 'app_ctx'):
        session.app_ctx.pop()

def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Auto-mark tests based on path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)