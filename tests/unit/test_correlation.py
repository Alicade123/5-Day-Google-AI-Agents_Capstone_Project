import pytest
from datetime import UTC, datetime, timedelta

from backend.memory.long_term import SQLiteLongTermMemory
from backend.models import SeverityLevel
from backend.models.incidents import Incident
from backend.services.correlation import IncidentCorrelationService
from backend.services.history import HistoryService


@pytest.mark.asyncio
async def test_correlate_cpu_spikes(tmp_path):
    db_path = str(tmp_path / "corr.db")
    memory = SQLiteLongTermMemory(db_path=db_path)
    history = HistoryService(db_path=db_path)
    service = IncidentCorrelationService(memory=memory, history=history)

    now = datetime.now(UTC)
    for i in range(3):
        incident = Incident(
            id=f"cpu-{i}",
            title=f"CPU spike {i}",
            summary="High CPU detected",
            severity=SeverityLevel.CRITICAL,
            facts=[f"CPU utilization is {90 + i}%"],
            created_at=now - timedelta(minutes=10 * i),
        )
        await memory.save_incident(incident)

    result = await service.analyze(window_hours=1)
    cpu_patterns = [p for p in result.patterns if p.pattern == "cpu_spike"]
    assert len(cpu_patterns) == 1
    assert cpu_patterns[0].frequency == 3
    assert cpu_patterns[0].severity == SeverityLevel.CRITICAL


@pytest.mark.asyncio
async def test_correlate_database_issues(tmp_path):
    db_path = str(tmp_path / "db_corr.db")
    memory = SQLiteLongTermMemory(db_path=db_path)
    history = HistoryService(db_path=db_path)
    service = IncidentCorrelationService(memory=memory, history=history)

    now = datetime.now(UTC)
    for i in range(2):
        incident = Incident(
            id=f"db-{i}",
            title="DB latency",
            summary="Database connection slow",
            severity=SeverityLevel.WARNING,
            facts=["Database is disconnected"],
            created_at=now - timedelta(minutes=5 * i),
        )
        await memory.save_incident(incident)

    result = await service.analyze(window_hours=1)
    db_patterns = [p for p in result.patterns if p.pattern == "database_latency"]
    assert len(db_patterns) == 1
    assert db_patterns[0].frequency == 2
