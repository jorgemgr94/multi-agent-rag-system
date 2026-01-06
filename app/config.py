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

    # Vector store configuration
    vector_store_type: str = "faiss"  # Options: faiss, pinecone

    # Pinecone (optional, only if vector_store_type=pinecone)
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "deal-intelligence"
    pinecone_environment: str = "us-east-1"


settings = Settings()  # type: ignore[call-arg]
