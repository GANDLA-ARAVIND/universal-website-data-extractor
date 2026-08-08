import uuid
from typing import Optional
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.auth_service import AuthService
from src.application.services.batch_service import BatchService
from src.application.services.crawl_service import CrawlService
from src.application.services.export_service import ExportService
from src.application.services.project_service import ProjectService
from src.core.config import settings
from src.core.security import decode_access_token
from src.db.models.user import User
from src.db.repositories.batch_repository import BatchRepository
from src.db.repositories.crawl_repository import CrawlRepository
from src.db.repositories.page_repository import PageRepository
from src.db.session import get_async_db


def get_auth_service(
    session: AsyncSession = Depends(get_async_db),
) -> AuthService:
    """Dependency provider yielding AuthService instance."""
    return AuthService(session)


def get_project_service(
    session: AsyncSession = Depends(get_async_db),
) -> ProjectService:
    """Dependency provider yielding ProjectService instance."""
    return ProjectService(session)


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


async def get_current_user_optional(
    access_token_cookie: Optional[str] = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    authorization: Optional[str] = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    """Extracts and verifies JWT token from Bearer header or HTTP-only cookie.
    Returns Optional[User] (None if unauthenticated) for public-friendly routes.
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif access_token_cookie:
        token = access_token_cookie

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        return None

    user = await auth_service.get_user_by_id(user_id)
    if not user or not user.is_active:
        return None

    return user


async def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Enforces active user authentication. Raises HTTP 401 Unauthorized if unauthenticated."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
