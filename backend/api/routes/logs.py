from fastapi import APIRouter, Depends

from backend.models.api import LogsResponse
from backend.services.metrics_collector import MetricsCollector

router = APIRouter(tags=["logs"])


def get_collector() -> MetricsCollector:
    return MetricsCollector()


@router.get("/logs", response_model=LogsResponse)
async def get_logs(collector: MetricsCollector = Depends(get_collector)) -> LogsResponse:
    results = await collector.collect_logs()
    failures = [f"{name}: {r.error}" for name, r in results.items() if not r.success]
    return LogsResponse(results=list(results.values()), failures=failures)
