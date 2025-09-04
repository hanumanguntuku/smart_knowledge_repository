"""
Test configuration and fixtures for Smart Knowledge Repository
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Test environment setup
os.environ["TESTING"] = "1"
os.environ["LOG_LEVEL"] = "ERROR"


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_db():
    """Create a temporary test database"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    yield temp_db.name
    # Cleanup
    try:
        os.unlink(temp_db.name)
    except OSError:
        pass


@pytest.fixture
def mock_storage_manager():
    """Mock storage manager for testing"""
    from src.storage.storage_manager import StorageManager
    mock = MagicMock(spec=StorageManager)
    mock.get_statistics.return_value = {
        'documents': {'active': 10, 'deleted': 2},
        'categories': 5,
        'total_documents': 12
    }
    return mock


@pytest.fixture
def mock_search_engine():
    """Mock search engine for testing"""
    from src.search.search_engine import SearchEngine
    mock = MagicMock(spec=SearchEngine)
    mock.search.return_value = []
    return mock


@pytest.fixture
def mock_web_scraper():
    """Mock web scraper for testing"""
    from src.crawlers.web_scraper import WebScraper
    mock = MagicMock(spec=WebScraper)
    mock.scrape_url.return_value = ("Test content", {"title": "Test"})
    return mock


@pytest.fixture
def mock_chatbot():
    """Mock chatbot for testing"""
    from src.ai.scope_chatbot import ScopeAwareChatbot
    mock = MagicMock(spec=ScopeAwareChatbot)
    mock.process_query.return_value = {
        'response': 'Test response',
        'sources': [],
        'confidence': 0.8
    }
    return mock


@pytest.fixture
def sample_document():
    """Sample document for testing"""
    return {
        'title': 'Test Document',
        'content': 'This is a test document for unit testing purposes.',
        'url': 'https://example.com/test',
        'domain': 'technology',
        'content_type': 'article',
        'language': 'en',
        'metadata': {'test': True}
    }


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        {
            'id': 1,
            'title': 'Test Result 1',
            'content': 'Content for test result 1',
            'score': 0.95,
            'url': 'https://example.com/1'
        },
        {
            'id': 2,
            'title': 'Test Result 2', 
            'content': 'Content for test result 2',
            'score': 0.85,
            'url': 'https://example.com/2'
        }
    ]


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("SQLITE_DB_PATH", ":memory:")
    monkeypatch.setenv("VECTOR_DB_PATH", "/tmp/test_chroma")
    monkeypatch.setenv("TESTING", "1")


# Test data directories
@pytest.fixture
def test_data_dir():
    """Test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup handled by OS
