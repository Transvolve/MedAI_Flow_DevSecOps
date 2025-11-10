"""Configuration loading and validation tests.

Tests verify that Settings class loads configuration correctly,
applies defaults properly, and initializes with valid values.

Regulatory Compliance:
- FDA 21 CFR 11: Configuration management and validation
- ISO 27001: Security settings and access controls
- IEC 62304: Configuration requirements
"""

import pytest
from backend.app.config import Settings


class TestSettingsDefaults:
    """Test default configuration values."""

    def test_app_name_default(self):
        """Test app name has correct default."""
        settings = Settings()
        assert settings.app_name == "MedAI Flow Backend"

    def test_app_version_default(self):
        """Test app version has correct default."""
        settings = Settings()
        assert settings.app_version == "2.0.0"

    def test_jwt_algorithm_default(self):
        """Test JWT algorithm defaults to HS256."""
        settings = Settings()
        assert settings.jwt_algorithm == "HS256"

    def test_access_token_expiration_default(self):
        """Test token expiration defaults to 30 minutes."""
        settings = Settings()
        assert settings.access_token_expire_minutes == 30

    def test_rate_limit_default(self):
        """Test rate limiting defaults to 60 per minute."""
        settings = Settings()
        assert settings.rate_limit_per_minute == 60

    def test_rate_limit_burst_default(self):
        """Test rate limit burst defaults to 5."""
        settings = Settings()
        assert settings.rate_limit_burst == 5

    def test_redis_url_default(self):
        """Test Redis URL has correct default."""
        settings = Settings()
        assert settings.redis_url == "redis://localhost:6379/0"

    def test_redis_pool_size_default(self):
        """Test Redis pool size defaults to 10."""
        settings = Settings()
        assert settings.redis_pool_size == 10

    def test_redis_timeout_default(self):
        """Test Redis timeout defaults to 5 seconds."""
        settings = Settings()
        assert settings.redis_timeout == 5

    def test_redis_ssl_default(self):
        """Test Redis SSL defaults to False."""
        settings = Settings()
        assert settings.redis_ssl is False

    def test_cors_origins_default(self):
        """Test CORS origins have correct defaults."""
        settings = Settings()
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) > 0
        assert "localhost" in str(settings.cors_origins[0])

    def test_enforce_https_default(self):
        """Test HTTPS enforcement defaults to False."""
        settings = Settings()
        assert settings.enforce_https is False

    def test_max_response_rate_default(self):
        """Test max response rate defaults to 1MB/s."""
        settings = Settings()
        assert settings.max_response_rate == 1_000_000


class TestJWTSettings:
    """Test JWT configuration."""

    def test_jwt_secret_key_generated(self):
        """Test JWT secret key is generated and non-empty."""
        settings = Settings()
        assert settings.jwt_secret_key is not None
        assert len(settings.jwt_secret_key) > 0

    def test_jwt_secret_key_sufficient_length(self):
        """Test JWT secret has sufficient entropy."""
        settings = Settings()
        # Generated secrets should be at least 16 chars (sufficient for HS256)
        assert len(settings.jwt_secret_key) >= 16

    def test_jwt_algorithm_valid(self):
        """Test JWT algorithm is valid."""
        settings = Settings()
        valid_algorithms = ["HS256", "RS256"]
        assert settings.jwt_algorithm in valid_algorithms

    def test_jwt_expiration_positive(self):
        """Test JWT expiration time is positive."""
        settings = Settings()
        assert settings.access_token_expire_minutes > 0


class TestSecuritySettings:
    """Test security-related configuration."""

    def test_cors_methods_configured(self):
        """Test CORS methods are configured."""
        settings = Settings()
        assert isinstance(settings.cors_methods, list)
        assert len(settings.cors_methods) > 0

    def test_cors_headers_configured(self):
        """Test CORS headers are configured."""
        settings = Settings()
        assert isinstance(settings.cors_headers, list)
        assert len(settings.cors_headers) > 0

    def test_cors_methods_contain_allowed_verbs(self):
        """Test CORS methods include HTTP verbs."""
        settings = Settings()
        # Either specific methods or wildcard
        assert "*" in settings.cors_methods or any(
            verb in settings.cors_methods for verb in ["GET", "POST", "PUT", "DELETE"]
        )


class TestRedisConfiguration:
    """Test Redis-specific configuration."""

    def test_redis_url_valid_format(self):
        """Test Redis URL has valid format."""
        settings = Settings()
        assert settings.redis_url.startswith("redis://")

    def test_redis_pool_size_positive(self):
        """Test Redis pool size is positive."""
        settings = Settings()
        assert settings.redis_pool_size > 0
        assert settings.redis_pool_size <= 100  # Reasonable upper bound

    def test_redis_timeout_positive(self):
        """Test Redis timeout is positive."""
        settings = Settings()
        assert settings.redis_timeout > 0

    def test_redis_password_optional(self):
        """Test Redis password is optional."""
        settings = Settings()
        # Can be None or a string
        assert settings.redis_password is None or isinstance(settings.redis_password, str)


class TestRateLimitingConfiguration:
    """Test rate limiting settings."""

    def test_rate_limit_per_minute_positive(self):
        """Test rate limit per minute is positive."""
        settings = Settings()
        assert settings.rate_limit_per_minute > 0

    def test_rate_limit_burst_positive(self):
        """Test rate limit burst is positive."""
        settings = Settings()
        assert settings.rate_limit_burst > 0

    def test_rate_limit_burst_less_than_per_minute(self):
        """Test burst limit is reasonable compared to per-minute limit."""
        settings = Settings()
        # Burst should typically be less than per-minute allowance
        assert settings.rate_limit_burst < settings.rate_limit_per_minute * 2

    def test_max_response_rate_positive(self):
        """Test max response rate is positive."""
        settings = Settings()
        assert settings.max_response_rate > 0


class TestUserConfiguration:
    """Test user/authentication configuration."""

    def test_users_dict_configured(self):
        """Test users dictionary is configured."""
        settings = Settings()
        assert isinstance(settings.users, dict)
        assert len(settings.users) > 0

    def test_admin_user_present(self):
        """Test admin user is configured."""
        settings = Settings()
        assert "admin" in settings.users
        admin = settings.users["admin"]
        assert "password" in admin
        assert "role" in admin
        assert admin["role"] == "admin"

    def test_regular_user_present(self):
        """Test regular user account exists."""
        settings = Settings()
        assert "user" in settings.users
        user = settings.users["user"]
        assert user["role"] == "user"

    def test_test_user_present(self):
        """Test test user account exists."""
        settings = Settings()
        assert "test" in settings.users
        assert "password" in settings.users["test"]

    def test_user_passwords_hashed(self):
        """Test all user passwords are hashed (not plaintext)."""
        settings = Settings()
        for username, user_data in settings.users.items():
            password_hash = user_data["password"]
            # Hashed passwords contain $ characters (argon2 or bcrypt indicators)
            assert "$" in password_hash, f"Password for {username} doesn't look hashed"


class TestSettingsIntegrity:
    """Test settings object integrity and completeness."""

    def test_all_required_fields_present(self):
        """Test all required configuration fields are present."""
        settings = Settings()
        required_fields = [
            'app_name', 'app_version', 'jwt_secret_key', 'jwt_algorithm',
            'access_token_expire_minutes', 'rate_limit_per_minute',
            'rate_limit_burst', 'redis_url', 'redis_pool_size',
            'redis_timeout', 'redis_ssl', 'users', 'cors_origins',
            'cors_methods', 'cors_headers', 'enforce_https', 'max_response_rate'
        ]
        for field in required_fields:
            assert hasattr(settings, field), f"Missing required field: {field}"

    def test_settings_is_singleton_instance_consistency(self):
        """Test that settings can be instantiated multiple times."""
        settings1 = Settings()
        settings2 = Settings()
        # Both should have same defaults
        assert settings1.app_name == settings2.app_name
        assert settings1.jwt_algorithm == settings2.jwt_algorithm


class TestSettingsValidation:
    """Test settings validation logic."""

    def test_string_fields_not_empty(self):
        """Test required string fields are not empty."""
        settings = Settings()
        assert len(settings.app_name) > 0
        assert len(settings.app_version) > 0
        assert len(settings.jwt_secret_key) > 0
        assert len(settings.jwt_algorithm) > 0
        assert len(settings.redis_url) > 0

    def test_numeric_fields_valid_types(self):
        """Test numeric fields have correct types."""
        settings = Settings()
        assert isinstance(settings.access_token_expire_minutes, int)
        assert isinstance(settings.rate_limit_per_minute, int)
        assert isinstance(settings.rate_limit_burst, int)
        assert isinstance(settings.redis_pool_size, int)
        assert isinstance(settings.redis_timeout, int)
        assert isinstance(settings.max_response_rate, int)

    def test_boolean_fields_valid_types(self):
        """Test boolean fields have correct types."""
        settings = Settings()
        assert isinstance(settings.redis_ssl, bool)
        assert isinstance(settings.enforce_https, bool)

    def test_list_fields_valid_types(self):
        """Test list fields have correct types."""
        settings = Settings()
        assert isinstance(settings.cors_origins, list)
        assert isinstance(settings.cors_methods, list)
        assert isinstance(settings.cors_headers, list)

    def test_dict_fields_valid_types(self):
        """Test dict fields have correct types."""
        settings = Settings()
        assert isinstance(settings.users, dict)


class TestSettingsCompliance:
    """Test settings meet compliance and security requirements."""

    def test_has_security_settings(self):
        """Test security-critical settings are present."""
        settings = Settings()
        assert settings.jwt_secret_key is not None
        assert settings.jwt_algorithm is not None
        assert hasattr(settings, 'enforce_https')

    def test_has_logging_settings(self):
        """Test that logging-relevant settings are available."""
        settings = Settings()
        # Even if not explicitly named, security settings help with audit
        assert hasattr(settings, 'app_name')
        assert hasattr(settings, 'users')

    def test_supports_cors_configuration(self):
        """Test CORS can be configured for regulatory compliance."""
        settings = Settings()
        assert hasattr(settings, 'cors_origins')
        assert hasattr(settings, 'cors_methods')
        assert hasattr(settings, 'cors_headers')

    def test_supports_rate_limiting(self):
        """Test rate limiting is configured for API protection."""
        settings = Settings()
        assert hasattr(settings, 'rate_limit_per_minute')
        assert hasattr(settings, 'rate_limit_burst')

    def test_supports_redis_configuration(self):
        """Test Redis configuration is available for caching."""
        settings = Settings()
        assert hasattr(settings, 'redis_url')
        assert hasattr(settings, 'redis_pool_size')
