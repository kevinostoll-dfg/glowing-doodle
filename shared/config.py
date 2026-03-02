"""Application configuration via Pydantic BaseSettings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://calliq:calliq@localhost:5432/calliq"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""

    # OpenAI
    openai_api_key: str = ""

    # Deepgram
    deepgram_api_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # S3-compatible storage
    s3_endpoint: str = ""
    s3_bucket: str = "call-recordings"
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # Application
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
