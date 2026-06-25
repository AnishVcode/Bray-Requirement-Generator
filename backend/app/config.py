"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ─── Application ───
    APP_NAME: str = "Requirement Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    MOCK_MODE: bool = False  # Set True for local dev without Azure
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    # ─── Azure OpenAI ───
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS: int = 3072

    # ─── Azure AI Search ───
    AZURE_SEARCH_ENDPOINT: str = ""
    AZURE_SEARCH_API_KEY: str = ""
    AZURE_SEARCH_INDEX_NAME: str = "code-requirements-index"

    # ─── Azure Blob Storage ───
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "generated-reports"

    # ─── Azure Key Vault ───
    AZURE_KEYVAULT_URL: str = ""

    # ─── Azure Monitor / App Insights ───
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = ""

    # ─── GitHub ───
    GITHUB_TOKEN: str = ""

    # ─── Processing ───
    MAX_REPO_SIZE_MB: int = 100
    MAX_FILES_TO_ANALYZE: int = 500
    CHUNK_SIZE_TOKENS: int = 800
    CHUNK_OVERLAP_TOKENS: int = 100
    MAX_CONCURRENT_PROCESSING: int = 5
    EMBEDDING_BATCH_SIZE: int = 16
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: float = 1.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
