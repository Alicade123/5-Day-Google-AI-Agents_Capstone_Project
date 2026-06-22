from pydantic import BaseModel, Field

from backend.models import ConfidenceLevel, SeverityLevel


class LogErrorEntry(BaseModel):
    line: int
    timestamp: str | None = None
    message: str
    level: str = "ERROR"


class ErrorPattern(BaseModel):
    pattern: str
    count: int
    severity: SeverityLevel = SeverityLevel.WARNING


class LogAnalysisResult(BaseModel):
    path: str
    lines_analyzed: int
    errors: list[LogErrorEntry] = Field(default_factory=list)
    patterns: list[ErrorPattern] = Field(default_factory=list)
    summary: str = ""


class AnomalyFinding(BaseModel):
    metric: str
    description: str
    severity: SeverityLevel
    observed_value: float | str | None = None
    threshold: float | None = None


class AgentResponse(BaseModel):
    facts: list[str] = Field(default_factory=list)
    possible_explanations: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    recommended_actions: list[str] = Field(default_factory=list)
    anomalies: list[AnomalyFinding] = Field(default_factory=list)
    insufficient_evidence: bool = False
    raw_tool_summary: dict | None = None
