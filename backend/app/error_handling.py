"""Enhanced error handling with compliance-aware error codes.

Provides consistent, secure error handling across the application with:
- Specific error codes for programmatic handling
- Safe error messages (no PHI/PII exposure)
- Error tracking for monitoring
- Compliance audit trail integration

Regulatory Compliance:
- FDA 21 CFR 11: Comprehensive error logging
- HIPAA: Error information without PHI disclosure
- ISO 27001: Security-related error handling
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Error categories for classification and handling."""

    # Input validation errors
    VALIDATION = "VALIDATION"
    # Authentication/authorization errors
    AUTH = "AUTH"
    # Resource not found errors
    NOT_FOUND = "NOT_FOUND"
    # Business logic errors
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    # System/infrastructure errors
    SYSTEM = "SYSTEM"
    # Rate limiting errors
    RATE_LIMIT = "RATE_LIMIT"
    # Database errors
    DATABASE = "DATABASE"
    # External service errors
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    # Configuration errors
    CONFIG = "CONFIG"


@dataclass
class ErrorCode:
    """Error code with severity and category."""

    code: str
    category: ErrorCategory
    http_status: int
    message: str
    severity: str  # INFO, WARNING, ERROR, CRITICAL


class ApplicationError(Exception):
    """Base application error with error code tracking.
    
    All application errors should inherit from this class to ensure
    consistent error handling and compliance logging.
    """

    # Dictionary of application error codes
    ERROR_CODES: Dict[str, ErrorCode] = {
        # Validation errors
        "VAL_001": ErrorCode(
            code="VAL_001",
            category=ErrorCategory.VALIDATION,
            http_status=400,
            message="Invalid input format",
            severity="WARNING",
        ),
        "VAL_002": ErrorCode(
            code="VAL_002",
            category=ErrorCategory.VALIDATION,
            http_status=400,
            message="Missing required field",
            severity="WARNING",
        ),
        "VAL_003": ErrorCode(
            code="VAL_003",
            category=ErrorCategory.VALIDATION,
            http_status=400,
            message="Input exceeds maximum length",
            severity="WARNING",
        ),
        # Authentication errors
        "AUTH_001": ErrorCode(
            code="AUTH_001",
            category=ErrorCategory.AUTH,
            http_status=401,
            message="Invalid credentials",
            severity="WARNING",
        ),
        "AUTH_002": ErrorCode(
            code="AUTH_002",
            category=ErrorCategory.AUTH,
            http_status=401,
            message="Token expired",
            severity="WARNING",
        ),
        "AUTH_003": ErrorCode(
            code="AUTH_003",
            category=ErrorCategory.AUTH,
            http_status=401,
            message="Invalid token",
            severity="WARNING",
        ),
        "AUTH_004": ErrorCode(
            code="AUTH_004",
            category=ErrorCategory.AUTH,
            http_status=403,
            message="Insufficient permissions",
            severity="WARNING",
        ),
        # Not found errors
        "NOT_FOUND_001": ErrorCode(
            code="NOT_FOUND_001",
            category=ErrorCategory.NOT_FOUND,
            http_status=404,
            message="Resource not found",
            severity="INFO",
        ),
        # Business logic errors
        "BIZ_001": ErrorCode(
            code="BIZ_001",
            category=ErrorCategory.BUSINESS_LOGIC,
            http_status=422,
            message="Business rule violation",
            severity="WARNING",
        ),
        "BIZ_002": ErrorCode(
            code="BIZ_002",
            category=ErrorCategory.BUSINESS_LOGIC,
            http_status=422,
            message="Insufficient data for operation",
            severity="WARNING",
        ),
        # Rate limiting errors
        "RATE_001": ErrorCode(
            code="RATE_001",
            category=ErrorCategory.RATE_LIMIT,
            http_status=429,
            message="Rate limit exceeded",
            severity="INFO",
        ),
        # Database errors
        "DB_001": ErrorCode(
            code="DB_001",
            category=ErrorCategory.DATABASE,
            http_status=500,
            message="Database connection error",
            severity="ERROR",
        ),
        "DB_002": ErrorCode(
            code="DB_002",
            category=ErrorCategory.DATABASE,
            http_status=500,
            message="Database transaction error",
            severity="ERROR",
        ),
        # System errors
        "SYS_001": ErrorCode(
            code="SYS_001",
            category=ErrorCategory.SYSTEM,
            http_status=500,
            message="Internal server error",
            severity="ERROR",
        ),
        "SYS_002": ErrorCode(
            code="SYS_002",
            category=ErrorCategory.SYSTEM,
            http_status=503,
            message="Service unavailable",
            severity="ERROR",
        ),
        # External service errors
        "EXT_001": ErrorCode(
            code="EXT_001",
            category=ErrorCategory.EXTERNAL_SERVICE,
            http_status=502,
            message="External service error",
            severity="ERROR",
        ),
    }

    def __init__(
        self,
        error_code: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize application error.
        
        Args:
            error_code: Error code (e.g., 'VAL_001')
            message: Override default message if needed
            details: Additional error details
        """
        self.error_code = error_code
        self.details = details or {}

        # Get error code definition or use generic if not found
        if error_code in self.ERROR_CODES:
            self.error_def = self.ERROR_CODES[error_code]
        else:
            self.error_def = ErrorCode(
                code=error_code,
                category=ErrorCategory.SYSTEM,
                http_status=500,
                message="Unknown error",
                severity="ERROR",
            )

        # Use provided message or default from code definition
        self.message = message or self.error_def.message

        super().__init__(f"[{error_code}] {self.message}")

    @property
    def category(self) -> ErrorCategory:
        """Get error category."""
        return self.error_def.category

    @property
    def http_status(self) -> int:
        """Get HTTP status code."""
        return self.error_def.http_status

    @property
    def severity(self) -> str:
        """Get error severity."""
        return self.error_def.severity

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API response.
        
        Returns:
            Error representation safe for API response (no internal details)
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "category": self.category.value,
        }

    def log_error(self, request_id: Optional[str] = None) -> None:
        """Log error with context for auditing.
        
        Args:
            request_id: Request correlation ID for tracing
        """
        log_data = {
            "error_code": self.error_code,
            "error_message": self.message,
            "category": self.category.value,
            "severity": self.severity,
            "details": self.details,
        }

        if request_id:
            log_data["request_id"] = request_id

        if self.severity == "CRITICAL":
            logger.critical("Critical error occurred", extra=log_data)
        elif self.severity == "ERROR":
            logger.error("Error occurred", extra=log_data)
        elif self.severity == "WARNING":
            logger.warning("Warning occurred", extra=log_data)
        else:
            logger.info("Info message", extra=log_data)


class ValidationError(ApplicationError):
    """Input validation error."""

    def __init__(
        self,
        field: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validation error.
        
        Args:
            field: Field that failed validation
            message: Error message
            details: Additional details
        """
        super().__init__(
            "VAL_001",
            message=message,
            details=details or {},
        )
        if field:
            self.field = field
            self.details["field"] = field


class AuthenticationError(ApplicationError):
    """Authentication error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize authentication error."""
        super().__init__("AUTH_001", message=message, details=details or {})


class AuthorizationError(ApplicationError):
    """Authorization error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize authorization error."""
        super().__init__("AUTH_004", message=message, details=details or {})


class NotFoundError(ApplicationError):
    """Resource not found error."""

    def __init__(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize not found error."""
        message = "Resource not found"
        if resource_type:
            message = f"{resource_type} not found"

        super().__init__(
            "NOT_FOUND_001",
            message=message,
            details=details or {},
        )

        if resource_type:
            self.details["resource_type"] = resource_type
        if resource_id:
            self.details["resource_id"] = resource_id


class RateLimitError(ApplicationError):
    """Rate limit exceeded error."""

    def __init__(
        self,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize rate limit error.
        
        Args:
            retry_after: Seconds to wait before retry
            details: Additional details
        """
        super().__init__(
            "RATE_001",
            message="Rate limit exceeded",
            details=details or {},
        )
        if retry_after:
            self.retry_after = retry_after
            self.details["retry_after"] = retry_after


class BusinessLogicError(ApplicationError):
    """Business logic error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize business logic error."""
        super().__init__("BIZ_001", message=message, details=details or {})


class DatabaseError(ApplicationError):
    """Database operation error."""

    def __init__(
        self,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize database error."""
        message = "Database error"
        if operation:
            message = f"Database {operation} error"

        super().__init__(
            "DB_001",
            message=message,
            details=details or {},
        )

        if operation:
            self.details["operation"] = operation


class ExternalServiceError(ApplicationError):
    """External service error."""

    def __init__(
        self,
        service: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize external service error."""
        message = "External service error"
        if service:
            message = f"{service} service error"

        super().__init__(
            "EXT_001",
            message=message,
            details=details or {},
        )

        if service:
            self.details["service"] = service


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> ApplicationError:
    """Convert any exception to ApplicationError for consistent handling.
    
    Args:
        error: Exception to convert
        context: Additional context
        
    Returns:
        ApplicationError instance
    """
    if isinstance(error, ApplicationError):
        return error

    # Log unexpected error
    logger.error(
        f"Unexpected error type: {type(error).__name__}",
        extra={"error": str(error), "context": context},
    )

    # Return generic system error
    return ApplicationError(
        "SYS_001",
        message="An unexpected error occurred",
        details={"original_error": str(error), **context} if context else {},
    )
