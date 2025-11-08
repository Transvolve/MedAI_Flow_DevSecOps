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

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_redis():
    # Create the connection pool mock first
    pool_mock = MagicMock()
    pool_mock.max_connections = 10
    pool_mock.size.return_value = 5
    pool_mock.pid = 12345

    # Create Redis mock with connection pool
    redis_mock = MagicMock(spec=Redis)
    redis_mock.ping.return_value = True
    redis_mock.get.side_effect = lambda x: b"test_value" if x == "test_key" else None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.connection_pool = pool_mock
    
    # Create Redis class mock that returns our instance
    redis_class_mock = MagicMock()
    redis_class_mock.return_value = redis_mock
    
    # Patch both the Redis class and get_secure_redis_client
    with patch('redis.Redis', redis_class_mock), \
         patch('backend.app.redis_security.Redis', redis_class_mock), \
         patch('backend.app.redis_security.get_secure_redis_client', return_value=redis_mock), \
         patch('backend.app.rate_limit.Redis', redis_class_mock):
        yield redis_mock

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

import pytest

from backend.app.redis_security import set_redis_client

@pytest.fixture(scope="session", autouse=True)
def mock_redis_client():
    """
    Fixture to replace the real Redis client with a fake one for the entire test session.
    This runs once before any tests start.
    """
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    set_redis_client(fake_redis)
    yield fake_redis
    fake_redis.flushall()

@pytest.fixture(scope="module")
def client():
    """
    Provides a TestClient for making requests to the FastAPI app in tests.
    """
    with TestClient(app) as c:
        yield c