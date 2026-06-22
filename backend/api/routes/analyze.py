from fastapi import APIRouter, Depends

from backend.agents.orchestrator import AgentOrchestrator
from backend.config.settings import get_settings
from backend.memory.long_term import SQLiteLongTermMemory
from backend.models.api import AnalysisResult, MetricsSnapshot
from backend.services.history import HistoryService
from backend.services.incidents import IncidentService

router = APIRouter(tags=["analyze"])


def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()


def _db_path() -> str:
    return get_settings().database_url.replace("sqlite+aiosqlite:///", "")


def get_incident_service() -> IncidentService:
    return IncidentService(SQLiteLongTermMemory(db_path=_db_path()))


def get_history_service() -> HistoryService:
    return HistoryService(db_path=_db_path())


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    incident_service: IncidentService = Depends(get_incident_service),
    history_service: HistoryService = Depends(get_history_service),
) -> AnalysisResult:
    result = await orchestrator.analyze_full()
    anomaly_count = len(result.anomalies)
    await history_service.record_from_snapshot(result.snapshot, anomaly_count=anomaly_count)
    if result.agent_response and result.agent_response.facts:
        await incident_service.record_from_analysis(
            title="Automated health analysis",
            response=result.agent_response,
        )
    return result
