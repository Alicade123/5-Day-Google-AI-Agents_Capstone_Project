from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.models import SeverityLevel, ToolResult
from backend.models.logs import AgentResponse, AnomalyFinding, LogAnalysisResult


class MetricsSnapshot(BaseModel):
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    system: dict[str, Any] = Field(default_factory=dict)
    infrastructure: dict[str, Any] = Field(default_factory=dict)
    services: dict[str, Any] = Field(default_factory=dict)
    logs: dict[str, Any] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)
    tool_count: int = 0
    success_count: int = 0


class AnalysisResult(BaseModel):
    snapshot: MetricsSnapshot
    anomalies: list[AnomalyFinding] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    possible_explanations: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    overall_severity: SeverityLevel = SeverityLevel.INFO
    agent_response: AgentResponse | None = None


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language monitoring question")
    session_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict[str, str] = Field(default_factory=dict)


class LogsResponse(BaseModel):
    results: list[ToolResult[LogAnalysisResult]] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
