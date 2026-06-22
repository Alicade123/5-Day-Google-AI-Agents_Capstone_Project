from datetime import UTC, datetime

from fastapi import APIRouter

from backend import __version__
from backend.config.settings import get_settings
from backend.memory.long_term import SQLiteLongTermMemory
from backend.models.api import HealthResponse
from backend.services.history import HistoryService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    services: dict[str, str] = {}

    try:
        memory = SQLiteLongTermMemory(db_path=db_path)
        await memory.initialize()
        services["incidents_db"] = "healthy"
    except Exception:
        services["incidents_db"] = "unhealthy"

    try:
        history = HistoryService(db_path=db_path)
        await history.initialize()
        services["history_db"] = "healthy"
    except Exception:
        services["history_db"] = "unhealthy"

    overall = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"

    return HealthResponse(
        status=overall,
        app_name=settings.app_name,
        version=__version__,
        timestamp=datetime.now(UTC),
        services=services,
    )
