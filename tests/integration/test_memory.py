import pytest

from backend.memory.long_term import SQLiteLongTermMemory
from backend.memory.short_term import InMemoryShortTermMemory
from backend.models import ConfidenceLevel, SeverityLevel
from backend.models.logs import AgentResponse
from backend.services.incidents import IncidentService


@pytest.mark.asyncio
async def test_sqlite_incident_persistence(tmp_path):
    db_path = str(tmp_path / "incidents.db")
    memory = SQLiteLongTermMemory(db_path=db_path)
    service = IncidentService(memory)

    response = AgentResponse(
        facts=["CPU utilization is 96%"],
        possible_explanations=["CPU exceeded critical threshold"],
        confidence=ConfidenceLevel.HIGH,
        recommended_actions=["Investigate top processes"],
    )
    incident = await service.record_from_analysis("High CPU", response)
    assert incident.id
    assert incident.severity == SeverityLevel.INFO

    stored = await memory.list_incidents()
    assert len(stored) == 1
    assert stored[0].title == "High CPU"


def test_short_term_memory_session():
    memory = InMemoryShortTermMemory()
    memory.add_observation("sess-1", {"query": "test"})
    context = memory.get_context("sess-1")
    assert len(context) == 1
    memory.clear("sess-1")
    assert memory.get_context("sess-1") == []
