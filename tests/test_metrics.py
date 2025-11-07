"""Integration tests for rate limiting metrics and alerts."""
import pytest
import time
import sys
from pathlib import Path
from prometheus_client.parser import text_string_to_metric_families
from fastapi.testclient import TestClient

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from backend.app.main import app
from backend.app.metrics import (
    RATE_LIMIT_HITS,
    RATE_LIMIT_EXCEEDED,
    REDIS_OPERATION_LATENCY,
    REDIS_CONNECTED,
    track_rate_limit_hit,
    track_rate_limit_exceeded,
    track_redis_operation,
    set_redis_connected
)
from backend.app.redis_security import get_secure_redis_client

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def redis_client():
    client = get_secure_redis_client()
    set_redis_connected(True)
    yield client
    set_redis_connected(False)

def test_rate_limit_metrics(test_client):
    """Test rate limit metrics collection."""
    # Track some rate limit hits
    track_rate_limit_hit("/api/test", "127.0.0.1", 59)
    track_rate_limit_hit("/api/test", "127.0.0.1", 58)
    
    # Track rate limit exceeded
    track_rate_limit_exceeded("/api/test", "127.0.0.1")
    
    # Get metrics
    response = test_client.get("/metrics")
    assert response.status_code == 200
    
    metrics = {
        metric.name: metric 
        for metric in text_string_to_metric_families(response.text)
    }
    
    # Verify rate limit hits
    hits = metrics.get("rate_limit_hits_total")
    assert hits is not None
    assert any(
        sample.value == 2 
        for sample in hits.samples 
        if sample.labels["endpoint"] == "/api/test"
    )
    
    # Verify rate limit exceeded
    exceeded = metrics.get("rate_limit_exceeded_total")
    assert exceeded is not None
    assert any(
        sample.value == 1 
        for sample in exceeded.samples 
        if sample.labels["endpoint"] == "/api/test"
    )

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
    metrics = {
        metric.name: metric 
        for metric in text_string_to_metric_families(
            TestClient(app).get("/metrics").text
        )
    }
    
    # Verify latency histogram
    latency = metrics.get("redis_operation_latency_seconds")
    assert latency is not None
    assert any(
        sample.labels["operation"] == "test_set" 
        for sample in latency.samples
    )

def test_redis_connection_metrics(redis_client):
    """Test Redis connection status metrics."""
    # Get metrics
    metrics = {
        metric.name: metric 
        for metric in text_string_to_metric_families(
            TestClient(app).get("/metrics").text
        )
    }
    
    # Verify connection status
    connected = metrics.get("redis_connected")
    assert connected is not None
    assert any(sample.value == 1 for sample in connected.samples)
    
    # Simulate disconnection
    set_redis_connected(False)
    
    metrics = {
        metric.name: metric 
        for metric in text_string_to_metric_families(
            TestClient(app).get("/metrics").text
        )
    }
    connected = metrics.get("redis_connected")
    assert any(sample.value == 0 for sample in connected.samples)

@pytest.mark.asyncio
async def test_alert_conditions(test_client, redis_client):
    """Test conditions that would trigger alerts."""
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
    
    metrics = {
        metric.name: metric 
        for metric in text_string_to_metric_families(response.text)
    }
    
    # Verify conditions that would trigger alerts
    hits = metrics.get("rate_limit_hits_total")
    assert hits is not None
    assert any(
        sample.value >= 55 
        for sample in hits.samples 
        if sample.labels["endpoint"] == "/api/test"
    )
    
    latency = metrics.get("redis_operation_latency_seconds")
    assert latency is not None
    assert any(
        sample.labels["operation"] == "slow_operation" 
        for sample in latency.samples
    )