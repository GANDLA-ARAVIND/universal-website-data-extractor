"""Security Headers and Rate Limiting Middlewares.

Enforces HTTP Security Headers (CSP, X-Frame-Options, HSTS, etc.) and
in-memory client IP sliding window rate limiting.
"""

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.config import settings
from src.core.logging import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard OWASP security headers to all HTTP responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        if getattr(settings, "ENABLE_SECURITY_HEADERS", True):
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiting middleware per client IP address."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_timestamps: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not getattr(settings, "ENABLE_RATE_LIMITING", True):
            return await call_next(request)

        # Exempt static assets and OpenAPI docs from rate limiting
        path = request.url.path
        if path.startswith("/app") or path in ("/", "/docs", "/redoc", "/openapi.json", "/favicon.ico"):
            return await call_next(request)

        client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "127.0.0.1")
        now = time.time()
        window_start = now - 60.0

        # Clean timestamps older than 60 seconds
        timestamps = [ts for ts in self.request_timestamps[client_ip] if ts > window_start]
        self.request_timestamps[client_ip] = timestamps

        max_limit = getattr(settings, "RATE_LIMIT_PER_MINUTE", self.requests_per_minute)
        if len(timestamps) >= max_limit:
            logger.warning(f"Rate limit exceeded for client IP {client_ip} on path {path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "type": "RateLimitExceededException",
                    "error_type": "https://errors.websiteintelligence.dev/rate-limit-exceeded",
                    "title": "Rate Limit Exceeded",
                    "status": 429,
                    "detail": f"Rate limit of {max_limit} requests per minute exceeded.",
                    "instance": path,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                headers={"Retry-After": "60"},
            )

        self.request_timestamps[client_ip].append(now)
        return await call_next(request)
