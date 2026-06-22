import uuid

from fastapi import APIRouter, Depends

from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.response import ResponseGenerator
from backend.memory.short_term import InMemoryShortTermMemory
from backend.models.api import AgentQueryRequest
from backend.models.logs import AgentResponse
from backend.services.incidents import IncidentService
from backend.memory.long_term import SQLiteLongTermMemory
from backend.config.settings import get_settings

router = APIRouter(tags=["agent"])

_short_term_memory = InMemoryShortTermMemory()


def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()


def get_incident_service() -> IncidentService:
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    return IncidentService(SQLiteLongTermMemory(db_path=db_path))


@router.post("/agent/query", response_model=AgentResponse)
async def agent_query(
    request: AgentQueryRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    incident_service: IncidentService = Depends(get_incident_service),
) -> AgentResponse:
    session_id = request.session_id or str(uuid.uuid4())
    response = await orchestrator.query(request.query)

    _short_term_memory.add_observation(
        session_id,
        {"query": request.query, "facts_count": len(response.facts)},
    )

    if response.anomalies and not response.insufficient_evidence:
        await incident_service.record_from_analysis(
            title=f"Query: {request.query[:80]}",
            response=response,
        )

    return response
