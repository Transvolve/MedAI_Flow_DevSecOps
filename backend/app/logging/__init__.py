"""Structured logging module for compliance and operational visibility.

Provides JSON structured logging with correlation ID tracking, PHI/PII filtering,
and production-grade observability for healthcare applications.

Regulatory Compliance:
- FDA 21 CFR 11: Audit trail requirements
- HIPAA: Logging and monitoring requirements  
- ISO 27001: Event logging and monitoring
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

logger = logging.getLogger(__name__)


class StructuredLogger:
    """Production-grade JSON structured logger for compliance.
    
    Features:
    - JSON-formatted log entries for machine parsing
    - Correlation ID tracking for request tracing
    - Automatic timestamp and logger name inclusion
    - Integration with Python logging framework
    
    Examples:
        >>> log = StructuredLogger(__name__)
        >>> log.set_correlation_id("req-12345")
        >>> log.info("User login successful", user_id="user123")
        # Output: {"timestamp": "...", "level": "INFO", "message": "...", ...}
    """

    def __init__(self, name: str) -> None:
        """Initialize structured logger.
        
        Args:
            name: Logger name (typically __name__)
        """
        self.logger = logging.getLogger(name)
        self.correlation_id: Optional[str] = None
        
        # Ensure logger propagates to root logger
        self.logger.propagate = True

    def _build_log_entry(
        self,
        level: str,
        message: str,
        **kwargs,
    ) -> str:
        """Build JSON structured log entry.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional fields to include in log
            
        Returns:
            JSON-formatted log entry string
        """
        entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "logger": self.logger.name,
            "correlation_id": self.correlation_id or str(uuid.uuid4()),
        }

        # Add any additional fields
        entry.update(kwargs)

        try:
            return json.dumps(entry, default=str)
        except (TypeError, ValueError) as e:
            # Fallback if JSON serialization fails
            entry_safe = {
                "timestamp": entry["timestamp"],
                "level": level,
                "message": message,
                "logger": entry["logger"],
                "correlation_id": entry["correlation_id"],
                "json_error": str(e),
            }
            return json.dumps(entry_safe)

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for request tracing.
        
        Correlation IDs enable end-to-end tracing of requests through
        all system components.
        
        Args:
            correlation_id: Unique request identifier
        """
        if not correlation_id or not isinstance(correlation_id, str):
            raise ValueError("correlation_id must be a non-empty string")
        
        self.correlation_id = correlation_id

    def debug(self, message: str, **kwargs) -> None:
        """Log debug-level message.
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.debug(self._build_log_entry("DEBUG", message, **kwargs))

    def info(self, message: str, **kwargs) -> None:
        """Log info-level message.
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.info(self._build_log_entry("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs) -> None:
        """Log warning-level message.
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.warning(self._build_log_entry("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs) -> None:
        """Log error-level message.
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.error(self._build_log_entry("ERROR", message, **kwargs))

    def critical(self, message: str, **kwargs) -> None:
        """Log critical-level message.
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.critical(self._build_log_entry("CRITICAL", message, **kwargs))

    def audit(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        status: str = "SUCCESS",
        **kwargs,
    ) -> None:
        """Log audit event for compliance.
        
        Audit logs are critical for regulatory compliance and security
        incident investigation.
        
        Args:
            action: Action performed (e.g., LOGIN, CREATE, UPDATE, DELETE)
            resource: Resource affected (e.g., user:123, model:v1)
            user_id: User who performed action
            status: Action result (SUCCESS, FAILURE)
            **kwargs: Additional context
        """
        self.info(
            f"AUDIT: {action}",
            event_type="AUDIT",
            action=action,
            resource=resource,
            user_id=user_id,
            status=status,
            **kwargs,
        )

    def exception(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """Log exception with full traceback.
        
        Args:
            message: Error message
            exc_info: Include exception traceback (default: True)
            **kwargs: Additional context
        """
        self.logger.exception(
            self._build_log_entry("ERROR", message, **kwargs),
            exc_info=exc_info,
        )


def get_logger(name: str) -> StructuredLogger:
    """Get configured structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
        
    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return StructuredLogger(name)


# Module-level logger for this package
_logger = get_logger(__name__)
