from abc import ABC, abstractmethod

from backend.models.incidents import Incident
from backend.models.logs import AgentResponse


class ShortTermMemory(ABC):
    @abstractmethod
    def add_observation(self, session_id: str, observation: dict) -> None: ...

    @abstractmethod
    def get_context(self, session_id: str) -> list[dict]: ...

    @abstractmethod
    def clear(self, session_id: str) -> None: ...


class LongTermMemory(ABC):
    @abstractmethod
    async def save_incident(self, incident: Incident) -> None: ...

    @abstractmethod
    async def list_incidents(self, limit: int = 50) -> list[Incident]: ...

    @abstractmethod
    async def get_incident(self, incident_id: str) -> Incident | None: ...


class IncidentRecorder(ABC):
    @abstractmethod
    async def record_from_analysis(
        self,
        title: str,
        response: AgentResponse,
    ) -> Incident: ...
