"""Configure pytest for the project."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from redis import Redis

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from fastapi.testclient import TestClient
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