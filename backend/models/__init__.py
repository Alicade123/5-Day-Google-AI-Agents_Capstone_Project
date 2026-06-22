from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SeverityLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ConfidenceLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ToolResult(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
