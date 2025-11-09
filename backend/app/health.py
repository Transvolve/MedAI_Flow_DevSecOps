"""Health check endpoints and system status monitoring.

Provides comprehensive health checks for the application, database connections,
external service connectivity, and system resource availability.

Regulatory Compliance:
- FDA 21 CFR 11: System availability and monitoring
- ISO 27001: Availability and resilience
- IEC 62304: System monitoring requirements
"""

from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import psutil
import logging

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class SystemHealth:
    """System health and resource monitoring."""

    def __init__(self):
        """Initialize system health monitor."""
        self.check_time: Optional[datetime] = None
        self.cpu_percent: float = 0.0
        self.memory_percent: float = 0.0
        self.disk_percent: float = 0.0

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics.
        
        Returns:
            Dictionary containing CPU, memory, and disk usage percentages
            
        Regulatory Mapping:
            - FDA 21 CFR 11: System monitoring
            - ISO 27001: Resource monitoring
        """
        self.check_time = datetime.utcnow()
        self.cpu_percent = psutil.cpu_percent(interval=0.1)
        self.memory_percent = psutil.virtual_memory().percent
        self.disk_percent = psutil.disk_usage('/').percent

        return {
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_percent": round(self.memory_percent, 2),
            "disk_percent": round(self.disk_percent, 2),
            "timestamp": self.check_time.isoformat() + "Z",
        }

    def get_health_status(self) -> HealthStatus:
        """Determine overall system health status.
        
        Returns:
            HealthStatus enum indicating system health
            
        Status Logic:
            UNHEALTHY: CPU > 95% OR Memory > 90% OR Disk > 90%
            DEGRADED: CPU > 80% OR Memory > 75% OR Disk > 75%
            HEALTHY: Otherwise
        """
        metrics = self.get_system_metrics()

        cpu = metrics["cpu_percent"]
        mem = metrics["memory_percent"]
        disk = metrics["disk_percent"]

        if cpu > 95 or mem > 90 or disk > 90:
            return HealthStatus.UNHEALTHY
        elif cpu > 80 or mem > 75 or disk > 75:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


class DatabaseHealth:
    """Database connectivity and health monitoring."""

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize database health checker.
        
        Args:
            connection_string: Database connection URL
        """
        self.connection_string = connection_string
        self.last_check: Optional[datetime] = None
        self.is_connected: bool = False

    def check_connection(self) -> Dict[str, Any]:
        """Check database connectivity.
        
        Returns:
            Dictionary with connection status and response time
            
        Regulatory Mapping:
            - FDA 21 CFR 11: Data storage availability
            - ISO 27001: Database availability
        """
        self.last_check = datetime.utcnow()
        
        # TODO: Implement actual database connection check
        # This would connect to PostgreSQL and execute a simple query
        # For now, return placeholder
        
        return {
            "status": "connected" if self.is_connected else "disconnected",
            "last_check": self.last_check.isoformat() + "Z",
            "response_time_ms": 0,
        }

    def get_health_status(self) -> HealthStatus:
        """Get database health status.
        
        Returns:
            HealthStatus indicating database health
        """
        if not self.is_connected:
            return HealthStatus.UNHEALTHY
        return HealthStatus.HEALTHY


class RedisHealth:
    """Redis cache connectivity and health monitoring."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis health checker.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.last_check: Optional[datetime] = None
        self.is_connected: bool = False

    def check_connection(self) -> Dict[str, Any]:
        """Check Redis connectivity.
        
        Returns:
            Dictionary with connection status and response time
            
        Regulatory Mapping:
            - FDA 21 CFR 11: Cache availability for rate limiting
            - ISO 27001: Service availability
        """
        self.last_check = datetime.utcnow()
        
        # TODO: Implement actual Redis connection check
        # This would connect to Redis and execute PING command
        # For now, return placeholder
        
        return {
            "status": "connected" if self.is_connected else "disconnected",
            "last_check": self.last_check.isoformat() + "Z",
            "response_time_ms": 0,
        }

    def get_health_status(self) -> HealthStatus:
        """Get Redis health status.
        
        Returns:
            HealthStatus indicating Redis health
        """
        if not self.is_connected:
            return HealthStatus.UNHEALTHY
        return HealthStatus.HEALTHY


class HealthCheckService:
    """Comprehensive health check service."""

    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        redis_url: Optional[str] = None,
    ):
        """Initialize health check service.
        
        Args:
            db_connection_string: Database connection URL
            redis_url: Redis connection URL
        """
        self.system = SystemHealth()
        self.database = DatabaseHealth(db_connection_string)
        self.redis = RedisHealth(redis_url)
        self.startup_time = datetime.utcnow()

    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health check report.
        
        Returns:
            Dictionary with health status of all components
            
        Regulatory Mapping:
            - FDA 21 CFR 11: System health monitoring
            - ISO 13485: Product monitoring
        """
        system_status = self.system.get_health_status()
        db_status = self.database.get_health_status()
        redis_status = self.redis.get_health_status()

        # Overall status is worst of all components
        statuses = [system_status, db_status, redis_status]
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
            "components": {
                "system": {
                    "status": system_status.value,
                    "metrics": self.system.get_system_metrics(),
                },
                "database": {
                    "status": db_status.value,
                    "connection": self.database.check_connection(),
                },
                "redis": {
                    "status": redis_status.value,
                    "connection": self.redis.check_connection(),
                },
            },
        }

    def is_ready(self) -> bool:
        """Check if system is ready to serve requests.
        
        Returns:
            True if all components are healthy, False otherwise
            
        Regulatory Mapping:
            - FDA 21 CFR 11: System readiness validation
        """
        health = self.get_comprehensive_health()
        return health["status"] != HealthStatus.UNHEALTHY.value

    def is_alive(self) -> bool:
        """Check if system is alive (minimal health check).
        
        Returns:
            True if system is operational, False otherwise
            
        Regulatory Mapping:
            - ISO 27001: Service availability
        """
        # System is alive if resources are available
        system_metrics = self.system.get_system_metrics()
        return (
            system_metrics["cpu_percent"] < 100
            and system_metrics["memory_percent"] < 100
            and system_metrics["disk_percent"] < 100
        )
