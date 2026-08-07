"""FastAPI Dependency Injection Providers.

Instantiates services with async database session lifecycle contexts.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.services.batch_service import BatchService
from src.application.services.crawl_service import CrawlService
from src.application.services.export_service import ExportService
from src.db.repositories.batch_repository import BatchRepository
from src.db.repositories.crawl_repository import CrawlRepository
from src.db.repositories.page_repository import PageRepository
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
    return ExportService(CrawlRepository(session), PageRepository(session))


def get_batch_service(
    session: AsyncSession = Depends(get_async_db),
) -> BatchService:
    """Dependency provider yielding initialized BatchService instance."""
    crawl_repo = CrawlRepository(session)
    batch_repo = BatchRepository(session)
    crawl_svc = CrawlService(session)
    return BatchService(batch_repo, crawl_repo, crawl_svc)
