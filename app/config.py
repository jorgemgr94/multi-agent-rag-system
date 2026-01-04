"""Application configuration with validation."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Required
    openai_api_key: SecretStr

    # Optional with defaults
    openai_model: str = "gpt-4o-mini"
    log_level: str = "INFO"
    log_structured: bool = False  # Set True for JSON logs in production


settings = Settings()  # type: ignore[call-arg]
