from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="MedAI Flow Backend")
    app_version: str = Field(default="1.0")

    # Security
    api_token: str = Field(default="test-token")  # Replace via env var in non-dev

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


