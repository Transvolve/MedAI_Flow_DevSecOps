"""Health check and system monitoring tests.

Tests for health check endpoints, system resource monitoring,
and component connectivity validation.

Regulatory Compliance:
- FDA 21 CFR 11: System availability and monitoring
- ISO 27001: Availability and resilience
- IEC 62304: System monitoring
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from backend.app.health import (
    HealthStatus,
    SystemHealth,
    DatabaseHealth,
    RedisHealth,
    HealthCheckService,
)


class TestHealthStatusEnum:
    """Test HealthStatus enumeration."""

    def test_health_status_values(self):
        """Test HealthStatus enum has correct values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_status_comparison(self):
        """Test HealthStatus values can be compared."""
        assert HealthStatus.HEALTHY != HealthStatus.UNHEALTHY
        assert HealthStatus.DEGRADED != HealthStatus.HEALTHY


class TestSystemHealth:
    """Test system resource health monitoring."""

    def test_system_health_initialization(self):
        """Test SystemHealth initializes correctly."""
        health = SystemHealth()
        assert health.check_time is None
        assert health.cpu_percent == 0.0
        assert health.memory_percent == 0.0
        assert health.disk_percent == 0.0

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_get_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection."""
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(percent=60.2)
        mock_disk.return_value = MagicMock(percent=70.8)

        health = SystemHealth()
        metrics = health.get_system_metrics()

        assert metrics["cpu_percent"] == 45.5
        assert metrics["memory_percent"] == 60.2
        assert metrics["disk_percent"] == 70.8
        assert "timestamp" in metrics
        assert health.check_time is not None

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_get_health_status_healthy(self, mock_disk, mock_memory, mock_cpu):
        """Test healthy status when resources are available."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        health = SystemHealth()
        status = health.get_health_status()

        assert status == HealthStatus.HEALTHY

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_get_health_status_degraded_high_cpu(self, mock_disk, mock_memory, mock_cpu):
        """Test degraded status when CPU is high."""
        mock_cpu.return_value = 85.0  # Above 80% threshold
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        health = SystemHealth()
        status = health.get_health_status()

        assert status == HealthStatus.DEGRADED

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_get_health_status_degraded_high_memory(self, mock_disk, mock_memory, mock_cpu):
        """Test degraded status when memory is high."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=80.0)  # Above 75% threshold
        mock_disk.return_value = MagicMock(percent=60.0)

        health = SystemHealth()
        status = health.get_health_status()

        assert status == HealthStatus.DEGRADED

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_get_health_status_unhealthy_critical_cpu(self, mock_disk, mock_memory, mock_cpu):
        """Test unhealthy status when CPU is critical."""
        mock_cpu.return_value = 96.0  # Above 95% threshold
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        health = SystemHealth()
        status = health.get_health_status()

        assert status == HealthStatus.UNHEALTHY

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_get_health_status_unhealthy_critical_memory(self, mock_disk, mock_memory, mock_cpu):
        """Test unhealthy status when memory is critical."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=91.0)  # Above 90% threshold
        mock_disk.return_value = MagicMock(percent=60.0)

        health = SystemHealth()
        status = health.get_health_status()

        assert status == HealthStatus.UNHEALTHY


class TestDatabaseHealth:
    """Test database connectivity monitoring."""

    def test_database_health_initialization(self):
        """Test DatabaseHealth initializes correctly."""
        db_url = "postgresql://localhost/testdb"
        health = DatabaseHealth(db_url)

        assert health.connection_string == db_url
        assert health.last_check is None
        assert health.is_connected is False

    def test_database_health_initialization_no_url(self):
        """Test DatabaseHealth with no connection string."""
        health = DatabaseHealth()
        assert health.connection_string is None

    def test_check_connection_disconnected(self):
        """Test connection check when disconnected."""
        health = DatabaseHealth()
        result = health.check_connection()

        assert result["status"] == "disconnected"
        assert "last_check" in result
        assert "response_time_ms" in result

    def test_check_connection_connected(self):
        """Test connection check when connected."""
        health = DatabaseHealth()
        health.is_connected = True
        result = health.check_connection()

        assert result["status"] == "connected"

    def test_database_health_status_disconnected(self):
        """Test database health status when disconnected."""
        health = DatabaseHealth()
        status = health.get_health_status()

        assert status == HealthStatus.UNHEALTHY

    def test_database_health_status_connected(self):
        """Test database health status when connected."""
        health = DatabaseHealth()
        health.is_connected = True
        status = health.get_health_status()

        assert status == HealthStatus.HEALTHY


class TestRedisHealth:
    """Test Redis connectivity monitoring."""

    def test_redis_health_initialization(self):
        """Test RedisHealth initializes correctly."""
        redis_url = "redis://localhost:6379"
        health = RedisHealth(redis_url)

        assert health.redis_url == redis_url
        assert health.last_check is None
        assert health.is_connected is False

    def test_redis_health_initialization_no_url(self):
        """Test RedisHealth with no connection string."""
        health = RedisHealth()
        assert health.redis_url is None

    def test_check_connection_disconnected(self):
        """Test Redis connection check when disconnected."""
        health = RedisHealth()
        result = health.check_connection()

        assert result["status"] == "disconnected"
        assert "last_check" in result
        assert "response_time_ms" in result

    def test_check_connection_connected(self):
        """Test Redis connection check when connected."""
        health = RedisHealth()
        health.is_connected = True
        result = health.check_connection()

        assert result["status"] == "connected"

    def test_redis_health_status_disconnected(self):
        """Test Redis health status when disconnected."""
        health = RedisHealth()
        status = health.get_health_status()

        assert status == HealthStatus.UNHEALTHY

    def test_redis_health_status_connected(self):
        """Test Redis health status when connected."""
        health = RedisHealth()
        health.is_connected = True
        status = health.get_health_status()

        assert status == HealthStatus.HEALTHY


class TestHealthCheckService:
    """Test comprehensive health check service."""

    def test_health_check_service_initialization(self):
        """Test HealthCheckService initializes correctly."""
        service = HealthCheckService()

        assert service.system is not None
        assert service.database is not None
        assert service.redis is not None
        assert service.startup_time is not None

    def test_health_check_service_with_urls(self):
        """Test HealthCheckService initialization with connection URLs."""
        db_url = "postgresql://localhost/testdb"
        redis_url = "redis://localhost:6379"

        service = HealthCheckService(db_url, redis_url)

        assert service.database.connection_string == db_url
        assert service.redis.redis_url == redis_url

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_get_comprehensive_health(self, mock_disk, mock_memory, mock_cpu):
        """Test comprehensive health report generation."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        service = HealthCheckService()
        health = service.get_comprehensive_health()

        assert "status" in health
        assert "timestamp" in health
        assert "uptime_seconds" in health
        assert "components" in health
        assert "system" in health["components"]
        assert "database" in health["components"]
        assert "redis" in health["components"]

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_comprehensive_health_all_healthy(self, mock_disk, mock_memory, mock_cpu):
        """Test comprehensive health when all components are healthy."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        service = HealthCheckService()
        service.database.is_connected = True
        service.redis.is_connected = True

        health = service.get_comprehensive_health()

        assert health["status"] == HealthStatus.HEALTHY.value
        assert health["components"]["system"]["status"] == HealthStatus.HEALTHY.value
        assert health["components"]["database"]["status"] == HealthStatus.HEALTHY.value
        assert health["components"]["redis"]["status"] == HealthStatus.HEALTHY.value

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_comprehensive_health_database_down(self, mock_disk, mock_memory, mock_cpu):
        """Test comprehensive health when database is down."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        service = HealthCheckService()
        service.database.is_connected = False  # Database is down
        service.redis.is_connected = True

        health = service.get_comprehensive_health()

        assert health["status"] == HealthStatus.UNHEALTHY.value
        assert health["components"]["database"]["status"] == HealthStatus.UNHEALTHY.value

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_is_ready_all_healthy(self, mock_disk, mock_memory, mock_cpu):
        """Test is_ready returns True when all healthy."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        service = HealthCheckService()
        service.database.is_connected = True
        service.redis.is_connected = True

        assert service.is_ready() is True

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_is_ready_unhealthy(self, mock_disk, mock_memory, mock_cpu):
        """Test is_ready returns False when unhealthy."""
        mock_cpu.return_value = 96.0  # Critical
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        service = HealthCheckService()
        assert service.is_ready() is False

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_is_alive(self, mock_disk, mock_memory, mock_cpu):
        """Test is_alive returns True when resources available."""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = MagicMock(percent=60.0)
        mock_disk.return_value = MagicMock(percent=70.0)

        service = HealthCheckService()
        assert service.is_alive() is True

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_is_alive_false_maxed_cpu(self, mock_disk, mock_memory, mock_cpu):
        """Test is_alive returns False when CPU is maxed."""
        mock_cpu.return_value = 100.0
        mock_memory.return_value = MagicMock(percent=60.0)
        mock_disk.return_value = MagicMock(percent=70.0)

        service = HealthCheckService()
        assert service.is_alive() is False


class TestHealthCheckReportFormat:
    """Test health check report formatting."""

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_health_report_has_required_fields(self, mock_disk, mock_memory, mock_cpu):
        """Test health report contains all required fields."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        service = HealthCheckService()
        health = service.get_comprehensive_health()

        required_fields = ["status", "timestamp", "uptime_seconds", "components"]
        for field in required_fields:
            assert field in health, f"Missing required field: {field}"

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_health_report_timestamp_valid(self, mock_disk, mock_memory, mock_cpu):
        """Test health report timestamp is valid ISO format."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        service = HealthCheckService()
        health = service.get_comprehensive_health()

        timestamp_str = health["timestamp"]
        assert timestamp_str.endswith("Z")
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp_str.rstrip('Z'))

    @patch('backend.app.health.psutil.cpu_percent')
    @patch('backend.app.health.psutil.virtual_memory')
    @patch('backend.app.health.psutil.disk_usage')
    def test_uptime_calculation(self, mock_disk, mock_memory, mock_cpu):
        """Test uptime is correctly calculated."""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=50.0)
        mock_disk.return_value = MagicMock(percent=60.0)

        service = HealthCheckService()
        health = service.get_comprehensive_health()

        uptime = health["uptime_seconds"]
        assert uptime >= 0
        assert isinstance(uptime, float)
