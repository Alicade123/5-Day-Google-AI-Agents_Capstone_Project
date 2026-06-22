from datetime import datetime

from pydantic import BaseModel, Field

from backend.models import SeverityLevel


class Incident(BaseModel):
    id: str
    title: str
    summary: str
    severity: SeverityLevel
    facts: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
