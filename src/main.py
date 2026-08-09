"""FastAPI Main Application Entrypoint.

Initializes FastAPI app instance, CORS middleware, global exception handlers,
database schema auto-creation lifespan, and REST API routing.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from datetime import datetime, timezone
from src.api.v1.router import api_v1_router
from src.application.services.auth_service import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
)
from src.application.services.project_service import ProjectNotFoundException
from src.core.config import settings
from src.core.exceptions import (
    BaseAppException,
    CrawlJobNotFoundException,
    ExportException,
    InvalidURLException,
)
from src.core.logging import logger
from src.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from src.db.base import Base
from src.db.session import async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI Lifespan Context Manager.

    Ensures database connection initialization and clean engine shutdown.
    Schema migrations are managed by Alembic.
    """
    logger.info("Initializing database connection pool...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database connection engine ready.")
    yield
    logger.info("Shutting down database engine...")
    await async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Register Security & Rate Limit Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# Configurable CORS Middleware Setup
cors_origins = getattr(settings, "CORS_ORIGINS", ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# RFC 7807 Problem Details Exception Handlers
@app.exception_handler(BaseAppException)
async def domain_exception_handler(
    request: Request, exc: BaseAppException
) -> JSONResponse:
    """Handles domain-specific application exceptions formatted as RFC 7807 Problem Details."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type = "internal-server-error"

    if isinstance(exc, InvalidURLException):
        status_code = status.HTTP_400_BAD_REQUEST
        error_type = "invalid-url"
    elif isinstance(exc, CrawlJobNotFoundException) or isinstance(exc, ProjectNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
        error_type = "not-found"
    elif isinstance(exc, ExportException):
        status_code = status.HTTP_400_BAD_REQUEST
        error_type = "export-error"
    elif isinstance(exc, UserAlreadyExistsException):
        status_code = status.HTTP_409_CONFLICT
        error_type = "user-already-exists"
    elif isinstance(exc, InvalidCredentialsException):
        status_code = status.HTTP_401_UNAUTHORIZED
        error_type = "invalid-credentials"

    logger.warning(f"Domain Exception [{status_code}] on {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=status_code,
        content={
            "type": exc.__class__.__name__,
            "error_type": f"https://errors.websiteintelligence.dev/{error_type}",
            "title": exc.__class__.__name__,
            "status": status_code,
            "detail": exc.message,
            "instance": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handles unhandled unexpected exceptions as RFC 7807 Problem Details."""
    logger.error(f"Unhandled Exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://errors.websiteintelligence.dev/internal-server-error",
            "title": "InternalServerError",
            "status": 500,
            "detail": "An internal server error occurred while processing the request.",
            "instance": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Include API V1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# Mount Static Frontend Single Page Application at /app
if os.path.exists("static"):
    app.mount("/app", StaticFiles(directory="static", html=True), name="static")


from fastapi.responses import JSONResponse, RedirectResponse

@app.get("/", summary="Health Check", tags=["Health"])
async def root_health_check(request: Request):
    """System Health Check endpoint. Redirects browser HTML requests to /app."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url="/app")
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "frontend": "/app",
    }
