from fastapi import APIRouter, Depends, Query

from backend.config.settings import get_settings
from backend.models.history import HistoryResponse, TrendsResponse
from backend.services.history import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


def get_history_service() -> HistoryService:
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    return HistoryService(db_path=db_path)


@router.get("", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(default=100, ge=1, le=1000),
    since_minutes: int | None = Query(default=None, ge=1),
    history: HistoryService = Depends(get_history_service),
) -> HistoryResponse:
    return await history.get_history(limit=limit, since_minutes=since_minutes)


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    window_minutes: int = Query(default=15, ge=5, le=1440),
    history: HistoryService = Depends(get_history_service),
) -> TrendsResponse:
    return await history.compute_trends(window_minutes=window_minutes)
