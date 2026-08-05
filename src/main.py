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

from src.api.v1.router import api_v1_router
from src.core.config import settings
from src.core.exceptions import (
    BaseAppException,
    CrawlJobNotFoundException,
    ExportException,
    InvalidURLException,
)
from src.core.logging import logger
from src.db.base import Base
from src.db.session import async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI Lifespan Context Manager.

    Auto-creates database tables on application startup.
    """
    logger.info("Initializing database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")
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

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(BaseAppException)
async def domain_exception_handler(
    request: Request, exc: BaseAppException
) -> JSONResponse:
    """Handles domain-specific application exceptions."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, InvalidURLException):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, CrawlJobNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ExportException):
        status_code = status.HTTP_400_BAD_REQUEST

    logger.warning(f"Domain Exception [{status_code}] on {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "type": exc.__class__.__name__},
    )


# Include API V1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# Mount Static Frontend Single Page Application at /app
if os.path.exists("static"):
    app.mount("/app", StaticFiles(directory="static", html=True), name="static")


@app.get("/", summary="Health Check", tags=["Health"])
async def root_health_check() -> dict:
    """System Health Check endpoint."""
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "frontend": "/app",
    }
