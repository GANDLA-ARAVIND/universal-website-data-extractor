"""Application Configuration Module.

Uses Pydantic BaseSettings to read, validate, and type-check environment
variables for database connections, application parameters, and crawler defaults.
"""

from typing import Any
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings and environment variable bindings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # General Settings
    PROJECT_NAME: str = "Universal Website Data Extractor"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    USE_SQLITE: bool = False  # Set to True for zero-config local dev without PostgreSQL
    SQLITE_DB_PATH: str = "./web_scraper.db"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_password"
    POSTGRES_DB: str = "web_scraper_db"

    # Crawler Default Parameters
    DEFAULT_MAX_DEPTH: int = 2
    DEFAULT_MAX_PAGES: int = 50
    DEFAULT_CRAWL_DELAY_SEC: float = 0.5
    FETCH_TIMEOUT_SEC: float = 15.0
    PLAYWRIGHT_HEADLESS: bool = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ASYNC_DATABASE_URI(self) -> str:
        """Constructs asynchronous database connection string (PostgreSQL or SQLite)."""
        if self.USE_SQLITE:
            return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
