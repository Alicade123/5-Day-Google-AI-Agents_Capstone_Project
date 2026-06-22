import time
from collections import defaultdict

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.config.settings import get_settings

logger = structlog.get_logger(__name__)

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Optional API key authentication. Skipped when API_KEY is not configured."""

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        if not settings.api_key or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        provided = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if provided != settings.api_key:
            logger.warning("auth_failed", path=request.url.path)
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory per-IP rate limiter."""

    def __init__(self, app, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self._limit = requests_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60
        self._hits[client_ip] = [t for t in self._hits[client_ip] if t > window_start]

        if len(self._hits[client_ip]) >= self._limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        self._hits[client_ip].append(now)
        return await call_next(request)
