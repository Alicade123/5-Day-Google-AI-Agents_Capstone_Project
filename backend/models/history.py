from datetime import datetime

from pydantic import BaseModel, Field

from backend.models import SeverityLevel


class MetricSnapshotRecord(BaseModel):
    id: str
    recorded_at: datetime
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent_max: float | None = None
    network_bytes_sent: int | None = None
    network_bytes_recv: int | None = None
    database_connected: bool | None = None
    database_latency_ms: float | None = None
    service_health_ok: bool | None = None
    anomaly_count: int = 0


class HistoryResponse(BaseModel):
    records: list[MetricSnapshotRecord] = Field(default_factory=list)
    total: int = 0


class TrendChange(BaseModel):
    metric: str
    description: str
    previous_avg: float
    current_avg: float
    window_minutes: int
    direction: str  # increasing | decreasing | stable
    sustained: bool = False
    severity: SeverityLevel = SeverityLevel.INFO


class TrendsResponse(BaseModel):
    observations: int
    window_minutes: int
    moving_averages: dict[str, float] = Field(default_factory=dict)
    trend_changes: list[TrendChange] = Field(default_factory=list)
    summaries: list[str] = Field(default_factory=list)
    current_vs_previous: dict[str, dict[str, float]] = Field(default_factory=dict)
