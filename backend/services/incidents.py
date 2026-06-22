import uuid
from datetime import UTC, datetime

from backend.memory.interfaces import IncidentRecorder, LongTermMemory
from backend.models import SeverityLevel
from backend.models.incidents import Incident
from backend.models.logs import AgentResponse


class IncidentService(IncidentRecorder):
    def __init__(self, memory: LongTermMemory) -> None:
        self._memory = memory

    async def record_from_analysis(self, title: str, response: AgentResponse) -> Incident:
        severity = SeverityLevel.INFO
        if response.anomalies:
            severities = [a.severity for a in response.anomalies]
            if SeverityLevel.CRITICAL in severities:
                severity = SeverityLevel.CRITICAL
            elif SeverityLevel.WARNING in severities:
                severity = SeverityLevel.WARNING

        summary = (
            "; ".join(response.facts[:3])
            if response.facts
            else "No facts collected"
        )
        incident = Incident(
            id=str(uuid.uuid4()),
            title=title,
            summary=summary,
            severity=severity,
            facts=response.facts,
            recommendations=response.recommended_actions,
            created_at=datetime.now(UTC),
        )
        await self._memory.save_incident(incident)
        return incident
