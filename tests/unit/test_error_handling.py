"""Unit tests for error handling module (2.3 deliverable).

Tests cover:
- Application error base class
- Specific error types (Validation, Auth, NotFound, etc)
- Error codes and categorization
- Error conversion and handling
- Safe error responses

Target Coverage: 100% of error handling module
"""

import pytest
from backend.app.error_handling import (
    ApplicationError,
    ErrorCode,
    ErrorCategory,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    BusinessLogicError,
    DatabaseError,
    ExternalServiceError,
    handle_error,
)


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_all_categories_defined(self):
        """Test that all error categories are defined."""
        categories = [
            ErrorCategory.VALIDATION,
            ErrorCategory.AUTH,
            ErrorCategory.NOT_FOUND,
            ErrorCategory.BUSINESS_LOGIC,
            ErrorCategory.SYSTEM,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.DATABASE,
            ErrorCategory.EXTERNAL_SERVICE,
            ErrorCategory.CONFIG,
        ]
        assert len(categories) == 9

    def test_category_string_value(self):
        """Test category string values."""
        assert ErrorCategory.VALIDATION.value == "VALIDATION"
        assert ErrorCategory.AUTH.value == "AUTH"
        assert ErrorCategory.NOT_FOUND.value == "NOT_FOUND"


class TestErrorCode:
    """Test ErrorCode dataclass."""

    def test_error_code_creation(self):
        """Test creating error code."""
        code = ErrorCode(
            code="TEST_001",
            category=ErrorCategory.VALIDATION,
            http_status=400,
            message="Test error",
            severity="WARNING",
        )
        assert code.code == "TEST_001"
        assert code.http_status == 400

    def test_error_code_properties(self):
        """Test error code properties."""
        code = ErrorCode(
            code="TEST_002",
            category=ErrorCategory.AUTH,
            http_status=401,
            message="Auth test",
            severity="ERROR",
        )
        assert code.category == ErrorCategory.AUTH
        assert code.severity == "ERROR"


class TestApplicationError:
    """Test ApplicationError base class."""

    def test_error_creation_with_code(self):
        """Test creating error with known code."""
        error = ApplicationError("VAL_001", message="Invalid input")
        assert error.error_code == "VAL_001"
        assert error.message == "Invalid input"

    def test_error_creation_unknown_code(self):
        """Test creating error with unknown code."""
        error = ApplicationError("UNKNOWN_999")
        assert error.error_code == "UNKNOWN_999"
        assert error.message == "Unknown error"

    def test_error_properties(self):
        """Test error properties."""
        error = ApplicationError("VAL_001")
        assert error.category == ErrorCategory.VALIDATION
        assert error.http_status == 400
        assert error.severity == "WARNING"

    def test_error_with_details(self):
        """Test error with additional details."""
        details = {"field": "email", "reason": "invalid format"}
        error = ApplicationError("VAL_001", details=details)
        assert error.details == details

    def test_error_to_dict(self):
        """Test converting error to dictionary."""
        error = ApplicationError("VAL_001", message="Test message")
        error_dict = error.to_dict()
        assert "error_code" in error_dict
        assert "message" in error_dict
        assert "category" in error_dict
        assert error_dict["error_code"] == "VAL_001"
        assert error_dict["message"] == "Test message"

    def test_error_to_dict_safe(self):
        """Test that error dict is safe for API response."""
        error = ApplicationError(
            "VAL_001",
            details={"sensitive": "data", "field": "email"},
        )
        error_dict = error.to_dict()
        # Details should not be in API response
        assert "details" not in error_dict

    def test_error_inheritance(self):
        """Test that ApplicationError inherits from Exception."""
        error = ApplicationError("SYS_001")
        assert isinstance(error, Exception)

    def test_error_string_representation(self):
        """Test error string representation."""
        error = ApplicationError("AUTH_001", message="Invalid credentials")
        error_str = str(error)
        assert "AUTH_001" in error_str
        assert "Invalid credentials" in error_str

    def test_error_log_error_method(self, caplog):
        """Test logging error."""
        import logging
        with caplog.at_level(logging.WARNING):
            error = ApplicationError("VAL_001")
            error.log_error(request_id="req-123")
        assert len(caplog.records) > 0


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_creation(self):
        """Test creating validation error."""
        error = ValidationError(
            field="email",
            message="Invalid email format",
        )
        assert error.error_code == "VAL_001"
        assert error.message == "Invalid email format"
        assert error.details["field"] == "email"

    def test_validation_error_without_field(self):
        """Test validation error without field."""
        error = ValidationError(message="Validation failed")
        assert error.error_code == "VAL_001"

    def test_validation_error_category(self):
        """Test validation error category."""
        error = ValidationError()
        assert error.category == ErrorCategory.VALIDATION
        assert error.http_status == 400


class TestAuthenticationError:
    """Test AuthenticationError class."""

    def test_authentication_error_creation(self):
        """Test creating authentication error."""
        error = AuthenticationError(message="Invalid credentials")
        assert error.error_code == "AUTH_001"
        assert error.category == ErrorCategory.AUTH
        assert error.http_status == 401

    def test_authentication_error_default_message(self):
        """Test authentication error with default message."""
        error = AuthenticationError()
        assert error.error_code == "AUTH_001"


class TestAuthorizationError:
    """Test AuthorizationError class."""

    def test_authorization_error_creation(self):
        """Test creating authorization error."""
        error = AuthorizationError(message="Insufficient permissions")
        assert error.error_code == "AUTH_004"
        assert error.category == ErrorCategory.AUTH
        assert error.http_status == 403

    def test_authorization_error_properties(self):
        """Test authorization error properties."""
        error = AuthorizationError()
        assert error.severity == "WARNING"


class TestNotFoundError:
    """Test NotFoundError class."""

    def test_not_found_error_creation(self):
        """Test creating not found error."""
        error = NotFoundError(
            resource_type="User",
            resource_id="user123",
        )
        assert error.error_code == "NOT_FOUND_001"
        assert error.category == ErrorCategory.NOT_FOUND
        assert error.http_status == 404

    def test_not_found_error_details(self):
        """Test not found error details."""
        error = NotFoundError(
            resource_type="Model",
            resource_id="model123",
        )
        assert error.details["resource_type"] == "Model"
        assert error.details["resource_id"] == "model123"

    def test_not_found_error_message(self):
        """Test not found error message."""
        error = NotFoundError(resource_type="Image")
        assert "Image" in error.message

    def test_not_found_error_no_details(self):
        """Test not found error without details."""
        error = NotFoundError()
        assert error.http_status == 404


class TestRateLimitError:
    """Test RateLimitError class."""

    def test_rate_limit_error_creation(self):
        """Test creating rate limit error."""
        error = RateLimitError(retry_after=60)
        assert error.error_code == "RATE_001"
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.http_status == 429
        assert error.retry_after == 60

    def test_rate_limit_error_without_retry(self):
        """Test rate limit error without retry info."""
        error = RateLimitError()
        assert error.error_code == "RATE_001"

    def test_rate_limit_error_details(self):
        """Test rate limit error details."""
        error = RateLimitError(retry_after=120)
        assert error.details["retry_after"] == 120


class TestBusinessLogicError:
    """Test BusinessLogicError class."""

    def test_business_logic_error_creation(self):
        """Test creating business logic error."""
        error = BusinessLogicError(
            message="Insufficient data for operation"
        )
        assert error.error_code == "BIZ_001"
        assert error.category == ErrorCategory.BUSINESS_LOGIC
        assert error.http_status == 422

    def test_business_logic_error_default(self):
        """Test business logic error with default message."""
        error = BusinessLogicError()
        assert error.error_code == "BIZ_001"


class TestDatabaseError:
    """Test DatabaseError class."""

    def test_database_error_creation(self):
        """Test creating database error."""
        error = DatabaseError(operation="SELECT")
        assert error.error_code == "DB_001"
        assert error.category == ErrorCategory.DATABASE
        assert error.http_status == 500

    def test_database_error_details(self):
        """Test database error details."""
        error = DatabaseError(operation="INSERT")
        assert error.details["operation"] == "INSERT"
        assert "INSERT" in error.message

    def test_database_error_without_operation(self):
        """Test database error without operation."""
        error = DatabaseError()
        assert error.error_code == "DB_001"


class TestExternalServiceError:
    """Test ExternalServiceError class."""

    def test_external_service_error_creation(self):
        """Test creating external service error."""
        error = ExternalServiceError(service="Payment Provider")
        assert error.error_code == "EXT_001"
        assert error.category == ErrorCategory.EXTERNAL_SERVICE
        assert error.http_status == 502

    def test_external_service_error_details(self):
        """Test external service error details."""
        error = ExternalServiceError(service="Email Service")
        assert error.details["service"] == "Email Service"
        assert "Email Service" in error.message

    def test_external_service_error_without_service(self):
        """Test external service error without service name."""
        error = ExternalServiceError()
        assert error.error_code == "EXT_001"


class TestHandleError:
    """Test handle_error function."""

    def test_handle_application_error(self):
        """Test handling application error."""
        original = ApplicationError("VAL_001")
        result = handle_error(original)
        assert result is original

    def test_handle_standard_exception(self):
        """Test converting standard exception."""
        original = ValueError("Test error")
        result = handle_error(original)
        assert isinstance(result, ApplicationError)
        assert result.error_code == "SYS_001"

    def test_handle_exception_with_context(self):
        """Test handling exception with context."""
        original = RuntimeError("Failed operation")
        context = {"operation": "process_image"}
        result = handle_error(original, context=context)
        assert result.details["operation"] == "process_image"

    def test_handle_generic_exception(self):
        """Test handling generic exception."""
        error = Exception("Unknown error")
        result = handle_error(error)
        assert isinstance(result, ApplicationError)
        assert result.http_status == 500


class TestErrorCodeCoverage:
    """Test all predefined error codes."""

    def test_validation_codes(self):
        """Test validation error codes."""
        assert "VAL_001" in ApplicationError.ERROR_CODES
        assert "VAL_002" in ApplicationError.ERROR_CODES
        assert "VAL_003" in ApplicationError.ERROR_CODES

    def test_auth_codes(self):
        """Test authentication error codes."""
        assert "AUTH_001" in ApplicationError.ERROR_CODES
        assert "AUTH_002" in ApplicationError.ERROR_CODES
        assert "AUTH_003" in ApplicationError.ERROR_CODES
        assert "AUTH_004" in ApplicationError.ERROR_CODES

    def test_not_found_codes(self):
        """Test not found error codes."""
        assert "NOT_FOUND_001" in ApplicationError.ERROR_CODES

    def test_business_logic_codes(self):
        """Test business logic error codes."""
        assert "BIZ_001" in ApplicationError.ERROR_CODES
        assert "BIZ_002" in ApplicationError.ERROR_CODES

    def test_rate_limit_codes(self):
        """Test rate limit error codes."""
        assert "RATE_001" in ApplicationError.ERROR_CODES

    def test_database_codes(self):
        """Test database error codes."""
        assert "DB_001" in ApplicationError.ERROR_CODES
        assert "DB_002" in ApplicationError.ERROR_CODES

    def test_system_codes(self):
        """Test system error codes."""
        assert "SYS_001" in ApplicationError.ERROR_CODES
        assert "SYS_002" in ApplicationError.ERROR_CODES

    def test_external_service_codes(self):
        """Test external service error codes."""
        assert "EXT_001" in ApplicationError.ERROR_CODES

    def test_all_codes_have_valid_status(self):
        """Test that all error codes have valid HTTP status."""
        for code, error_def in ApplicationError.ERROR_CODES.items():
            assert 400 <= error_def.http_status < 600
            assert error_def.severity in ["INFO", "WARNING", "ERROR", "CRITICAL"]


class TestErrorSafety:
    """Test error safety for API responses."""

    def test_error_dict_no_sensitive_details(self):
        """Test that error dict doesn't expose internal details."""
        error = ApplicationError(
            "VAL_001",
            details={
                "field": "password",
                "internal_error": "bcrypt verification failed",
            },
        )
        error_dict = error.to_dict()
        assert "details" not in error_dict
        assert "internal_error" not in error_dict

    def test_validation_error_field_not_exposed(self):
        """Test that internal field details aren't exposed."""
        error = ValidationError(
            field="credit_card",
            message="Invalid format",
        )
        error_dict = error.to_dict()
        assert "details" not in error_dict

    def test_database_error_query_not_exposed(self):
        """Test that database queries aren't exposed."""
        error = DatabaseError(
            operation="SELECT * FROM users",
            details={"sql": "SELECT * FROM users WHERE id=1"},
        )
        error_dict = error.to_dict()
        # SQL should not be in API response
        assert "details" not in error_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
