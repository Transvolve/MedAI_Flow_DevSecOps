# tests/test_metrics.py
"""Integration tests for rate limiting metrics and alerts."""
from pathlib import Path
import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from backend.app.main import app  # noqa: E402
from backend.app.metrics import (  # noqa: E402
    track_rate_limit_hit,
    track_rate_limit_exceeded,
    track_redis_operation,
    set_redis_connected,
)


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def redis_client():
    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = "test_value"
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    # Mock connection pool attributes that tests read
    redis_mock.connection_pool = MagicMock()
    redis_mock.connection_pool.max_connections = 10
    redis_mock.connection_pool.size.return_value = 5
    redis_mock.connection_pool.pid = 12345

    with patch("backend.app.redis_security.get_secure_redis_client", return_value=redis_mock):
        set_redis_connected(True)
        yield redis_mock
        set_redis_connected(False)


def test_rate_limit_metrics(test_client):
    """Test rate limit metrics collection."""
    from prometheus_client import REGISTRY
    
    # Track some rate limit hits
    track_rate_limit_hit("/api/test", "127.0.0.1", 59)
    track_rate_limit_hit("/api/test", "127.0.0.1", 58)

    # Track rate limit exceeded
    track_rate_limit_exceeded("/api/test", "127.0.0.1")

    # Get metrics
    response = test_client.get("/metrics")
    assert response.status_code == 200

    metric_text = response.text
    metrics = list(text_string_to_metric_families(metric_text))

    # Debug: print all metric names
    if not metrics:
        # If no metrics, try to get from registry directly
        from prometheus_client import generate_latest
        metric_text = generate_latest(REGISTRY).decode('utf-8')
        metrics = list(text_string_to_metric_families(metric_text))

    # Find rate limit hits metric (Prometheus adds _total suffix to Counter internally, but base name is rate_limit_hits)
    hits_metric = next((m for m in metrics if m.name == "rate_limit_hits"), None)
    assert hits_metric is not None, f"rate_limit_hits metric not found. Available: {[m.name for m in metrics]}"

    # Verify hit count
    test_endpoint_hits = next(
        (s.value for s in hits_metric.samples if s.labels.get("endpoint") == "/api/test"),
        None,
    )
    assert test_endpoint_hits == 2, f"Expected 2 hits but found {test_endpoint_hits}"

    # Find rate limit exceeded metric
    exceeded_metric = next((m for m in metrics if m.name == "rate_limit_exceeded"), None)
    assert exceeded_metric is not None, "rate_limit_exceeded metric not found"

    # Verify exceeded count
    test_endpoint_exceeded = next(
        (s.value for s in exceeded_metric.samples if s.labels.get("endpoint") == "/api/test"),
        None,
    )
    assert test_endpoint_exceeded == 1, f"Expected 1 exceeded but found {test_endpoint_exceeded}"


@pytest.mark.asyncio
async def test_redis_latency_metrics(redis_client):
    """Test Redis operation latency metrics."""

    @track_redis_operation("test_set")
    def test_redis_op():
        redis_client.set("test_key", "test_value")
        time.sleep(0.1)  # Simulate latency
        return redis_client.get("test_key")

    # Perform Redis operation
    result = test_redis_op()
    assert result == "test_value"

    # Get metrics
    response = TestClient(app).get("/metrics")
    metrics = list(text_string_to_metric_families(response.text))

    # Find Redis latency metric
    latency_metric = next((m for m in metrics if m.name == "redis_operation_latency_seconds"), None)
    assert latency_metric is not None, "redis_operation_latency_seconds metric not found"

    # Verify latency was recorded
    test_ops = [s for s in latency_metric.samples if s.labels.get("operation") == "test_set"]
    assert len(test_ops) > 0, "No test operations tracked"


def test_redis_connection_metrics(redis_client):
    """Test Redis connection status metrics."""
    # Get metrics
    metrics = list(text_string_to_metric_families(TestClient(app).get("/metrics").text))

    # Find redis connection metric
    connected_metric = next((m for m in metrics if m.name == "redis_connected"), None)
    assert connected_metric is not None, "redis_connected metric not found"

    # Verify connection status
    assert any(sample.value == 1 for sample in connected_metric.samples)

    # Simulate disconnection
    set_redis_connected(False)

    # Get updated metrics
    metrics = list(text_string_to_metric_families(TestClient(app).get("/metrics").text))

    # Find redis connection metric
    connected_metric = next((m for m in metrics if m.name == "redis_connected"), None)
    assert connected_metric is not None, "redis_connected metric not found"

    # Verify disconnection status
    assert any(sample.value == 0 for sample in connected_metric.samples)


@pytest.mark.asyncio
async def test_alert_conditions(test_client, redis_client):
    """Test conditions that would trigger alerts."""
    from prometheus_client import REGISTRY
    
    # Simulate high rate limit usage
    for _ in range(55):  # 90%+ of 60/minute limit
        track_rate_limit_hit("/api/test", "127.0.0.1", 5)

    # Simulate Redis latency
    @track_redis_operation("slow_operation")
    def slow_redis_op():
        time.sleep(0.15)  # > 100ms threshold
        return redis_client.get("test_key")

    slow_redis_op()

    # Get metrics
    response = test_client.get("/metrics")
    assert response.status_code == 200

    metric_text = response.text
    metrics = list(text_string_to_metric_families(metric_text))

    # Debug: fallback to registry if needed
    if not metrics:
        from prometheus_client import generate_latest
        metric_text = generate_latest(REGISTRY).decode('utf-8')
        metrics = list(text_string_to_metric_families(metric_text))

    # Find rate limit hits metric (base name is rate_limit_hits, not _total)
    hits_metric = next((m for m in metrics if m.name == "rate_limit_hits"), None)
    assert hits_metric is not None, f"rate_limit_hits metric not found. Available: {[m.name for m in metrics]}"

    # Verify high rate limit usage
    test_endpoint_hits = next(
        (s.value for s in hits_metric.samples if s.labels.get("endpoint") == "/api/test"),
        None,
    )
    assert test_endpoint_hits >= 55, f"Expected >=55 hits but found {test_endpoint_hits}"

    # Find Redis latency metric
    latency_metric = next((m for m in metrics if m.name == "redis_operation_latency_seconds"), None)
    assert latency_metric is not None, "redis_operation_latency_seconds metric not found"

    # Verify slow operation was tracked
    slow_ops = [s for s in latency_metric.samples if s.labels.get("operation") == "slow_operation"]
    assert len(slow_ops) > 0, "No slow operations tracked"
