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
    MAX_CONCURRENT_BATCH_JOBS: int = 3

    # Phase 1 Security & Hardening Settings
    ENABLE_SSRF_PROTECTION: bool = True
    ALLOW_PRIVATE_IPS: bool = False
    CORS_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ]
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    LOG_FORMAT: str = "json"

    # Phase 4 Auth & JWT Settings
    SECRET_KEY: str = "production-secret-key-change-in-env-9876543210"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    AUTH_COOKIE_NAME: str = "access_token"
    AUTH_COOKIE_SECURE: bool = False

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
