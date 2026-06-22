from fastapi import APIRouter, Depends, Query

from backend.config.settings import get_settings
from backend.memory.long_term import SQLiteLongTermMemory
from backend.models.correlation import CorrelationPatternResponse, CorrelationResponse
from backend.services.correlation import IncidentCorrelationService
from backend.services.history import HistoryService

router = APIRouter(tags=["correlation"])


def get_correlation_service() -> IncidentCorrelationService:
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    return IncidentCorrelationService(
        memory=SQLiteLongTermMemory(db_path=db_path),
        history=HistoryService(db_path=db_path),
    )


@router.get("/correlation", response_model=CorrelationResponse)
async def get_correlation(
    window_hours: int = Query(default=1, ge=1, le=168),
    service: IncidentCorrelationService = Depends(get_correlation_service),
) -> CorrelationResponse:
    result = await service.analyze(window_hours=window_hours)
    return CorrelationResponse(
        window_hours=result.window_hours,
        patterns=[
            CorrelationPatternResponse(
                pattern=p.pattern,
                frequency=p.frequency,
                severity=p.severity,
                confidence=p.confidence,
                description=p.description,
                related_incidents=p.related_incidents,
            )
            for p in result.patterns
        ],
    )
