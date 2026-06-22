from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import __version__
from backend.api.middleware import RequestTracingMiddleware, configure_logging
from backend.api.routes import agent, analyze, correlation, eval, health, history, incidents, logs, metrics
from backend.api.security import APIKeyAuthMiddleware, RateLimitMiddleware
from backend.config.settings import get_settings
from backend.memory.long_term import SQLiteLongTermMemory
from backend.services.history import HistoryService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    memory = SQLiteLongTermMemory(db_path=db_path)
    await memory.initialize()
    history = HistoryService(db_path=db_path)
    await history.initialize()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Intelligent Server Health Monitoring Agent API",
        lifespan=lifespan,
    )
    origins = settings.csv_list(settings.cors_origins) or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
    app.add_middleware(APIKeyAuthMiddleware)
    app.add_middleware(RequestTracingMiddleware)
    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(logs.router)
    app.include_router(analyze.router)
    app.include_router(agent.router)
    app.include_router(incidents.router)
    app.include_router(history.router)
    app.include_router(correlation.router)
    app.include_router(eval.router)
    return app


app = create_app()
