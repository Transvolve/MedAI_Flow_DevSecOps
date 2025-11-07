from typing import Dict
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
import secrets


class Settings(BaseSettings):
    app_name: str = Field(default="MedAI Flow Backend")
    app_version: str = Field(default="1.0")

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
    )    # Demo users (in production, use a database)
    users: Dict = {
        "admin": {
            "password": "$argon2id$v=19$m=65536,t=3,p=4$FKJUqpWy9h4jZOxdC0EI4Q$uG9gxokv2k7brFz4+ef3/yiajKW+pnJhwwSIGrGVxCw",  # argon2 hash for 'admin123'
            "role": "admin"
        },
        "user": {
            "password": "$argon2id$v=19$m=65536,t=3,p=4$EwIgJCTknPP+v/deS8k5xw$NY9THe9RspGhCkCH+NLhSn0dl3+y2Ef/MbS/djvkoVs",  # argon2 hash for 'user123'
            "role": "user"
        },
        "test": {
            "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # hashed 'test'
            "role": "user"
        }
    }

    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "https://app.medaiflow.com"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # Response Rate Limits (bytes/second)
    max_response_rate: int = 1_000_000  # 1MB/s

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

