from fastapi import APIRouter, Depends

from backend.config.settings import get_settings
from backend.models.api import MetricsSnapshot
from backend.services.history import HistoryService
from backend.services.metrics_collector import MetricsCollector

router = APIRouter(tags=["metrics"])


def get_collector() -> MetricsCollector:
    return MetricsCollector()


def get_history_service() -> HistoryService:
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    return HistoryService(db_path=db_path)


@router.get("/metrics", response_model=MetricsSnapshot)
async def get_metrics(
    collector: MetricsCollector = Depends(get_collector),
    history_service: HistoryService = Depends(get_history_service),
) -> MetricsSnapshot:
    snapshot = await collector.collect_full_snapshot()
    await history_service.record_from_snapshot(snapshot, anomaly_count=0)
    return snapshot
