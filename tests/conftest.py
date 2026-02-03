"""Configure pytest for the project."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from redis import Redis
import fakeredis

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from backend.app.main import app
from backend.app.redis_security import get_secure_redis_client, set_redis_client


@pytest.fixture(scope="session", autouse=True)
def mock_redis_client():
    """
    Fixture to replace the real Redis client with a fake one for the entire test session.
    This runs once before any tests start and applies to all tests.
    """
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    set_redis_client(fake_redis)
    yield fake_redis
    fake_redis.flushall()


@pytest.fixture
def test_client():
    """Fixture providing a TestClient for a single test."""
    return TestClient(app)


@pytest.fixture(scope="module")
def client():
    """
    Provides a TestClient for making requests to the FastAPI app in tests.
    Module-scoped to reuse client across tests within a module.
    """
    with TestClient(app) as c:
        yield c