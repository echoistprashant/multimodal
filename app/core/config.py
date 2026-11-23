"""Application Configuration Module.

Uses pydantic-settings to manage environment-specific configurations
with typed fields, default fallbacks, and validation.
"""

from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global system configuration settings."""

    # Project metadata
    PROJECT_NAME: str = "Multimodal Document Intelligence System"
    API_V1_STR: str = "/api/v1"
    ENV: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False

    # Server binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database & Storage
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/mdis_db",
        description="Async PostgreSQL connection string",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and task queue",
    )
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = "./storage"

    # S3 / MinIO Configuration (Optional for local mode)
    S3_ENDPOINT: str | None = None
    S3_BUCKET: str = "mdis-docs"
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_REGION: str = "us-east-1"

    # Document & Pipeline Constraints
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    MAX_PAGES_PER_DOCUMENT: int = 100
    RENDER_DPI: int = 200
    OCR_ENGINE: Literal["tesseract", "paddleocr", "doctr", "mock"] = "tesseract"
    CONFIDENCE_AUTO_APPROVE_THRESHOLD: float = 0.85

    # Multimodal & LLM Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024
    VLM_PROVIDER: Literal["gemini", "local", "mock"] = "gemini"
    VLM_MODEL: str = "gemini-1.5-flash"
    LLM_API_KEY: str = "mock-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
