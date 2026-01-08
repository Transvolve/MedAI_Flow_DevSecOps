from typing import Dict
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, model_validator
import secrets


class Settings(BaseSettings):
    app_name: str = Field(default="MedAI Flow Backend")
    app_version: str = Field(default="2.0.0")

    # Security Settings
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 5

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for rate limiting"
    )
    redis_pool_size: int = Field(
        default=10,
        description="Maximum number of Redis connections in the pool"
    )
    redis_timeout: int = Field(
        default=5,
        description="Redis operation timeout in seconds"
    )
    redis_ssl: bool = Field(
        default=False,
        description="Enable SSL for Redis connection"
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password for authentication"
    )
    # Demo users (in production, use a database)
    users: Dict = {
        "admin": {
            "password": "$argon2id$v=19$m=65536,t=3,p=4$FKJUqpWy9h4jZOxdC"
            "0EI4Q$uG9gxokv2k7brFz4+ef3/yiajKW+pnJhwwSIGrGVxCw",
            "role": "admin"
        },
        "user": {
            "password": "$argon2id$v=19$m=65536,t=3,p=4$EwIgJCTknPP+v/deS8"
            "k5xw$NY9THe9RspGhCkCH+NLhSn0dl3+y2Ef/MbS/djvkoVs",
            "role": "user"
        },
        "test": {
            "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OX"
            "ePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            "role": "user"
        }
    }

    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "https://app.medaiflow.com"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # HTTPS Enforcement
    enforce_https: bool = Field(
        default=True,
        description="Enforce HTTPS for all incoming requests"
    )

    # Response Rate Limits (bytes/second)
    max_response_rate: int = 1_000_000  # 1MB/s

    @model_validator(mode='after')
    def load_users_and_check_security(self) -> 'Settings':
        # Load users from USERS_JSON environment variable if present
        import os
        import json
        import warnings
        
        users_json = os.environ.get("USERS_JSON")
        if users_json:
            try:
                self.users = json.loads(users_json)
            except json.JSONDecodeError:
                warnings.warn("Invalid JSON in USERS_JSON environment variable. Falling back to default users.")
        
        # Check for hardcoded default users (Security Warning)
        default_admin_hash_start = "$argon2id$v=19$m=65536,t=3,p=4$FKJUqpWy9h4jZOxdC"
        if "admin" in self.users:
            # We check if the password matches the hardcoded one partly
            password = self.users["admin"].get("password", "")
            if password.startswith(default_admin_hash_start):
                 warnings.warn("SECURITY WARNING: Using default hardcoded users in config.py. Configure USERS_JSON for production!", UserWarning)

        return self

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

