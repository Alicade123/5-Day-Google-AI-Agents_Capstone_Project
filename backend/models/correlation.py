from pydantic import BaseModel, Field

from backend.models import ConfidenceLevel, SeverityLevel


class CorrelationPatternResponse(BaseModel):
    pattern: str
    frequency: int
    severity: SeverityLevel
    confidence: ConfidenceLevel
    description: str
    related_incidents: list[str] = Field(default_factory=list)


class CorrelationResponse(BaseModel):
    window_hours: int
    patterns: list[CorrelationPatternResponse] = Field(default_factory=list)
