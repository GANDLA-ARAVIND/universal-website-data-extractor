"""FastAPI Dependency Injection Providers.

Instantiates services with async database session lifecycle contexts.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.services.crawl_service import CrawlService
from src.application.services.export_service import ExportService
from src.db.session import get_async_db


def get_crawl_service(
    session: AsyncSession = Depends(get_async_db),
) -> CrawlService:
    """Dependency provider yielding initialized CrawlService instance."""
    return CrawlService(session)


def get_export_service(
    session: AsyncSession = Depends(get_async_db),
) -> ExportService:
    """Dependency provider yielding initialized ExportService instance."""
    return ExportService(session)
