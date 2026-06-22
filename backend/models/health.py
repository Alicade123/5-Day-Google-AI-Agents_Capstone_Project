from datetime import datetime

from pydantic import BaseModel, Field


class PingResult(BaseModel):
    host: str
    latency_ms: float | None = None
    reachable: bool


class HttpHealthResult(BaseModel):
    url: str
    status_code: int | None = None
    response_time_ms: float | None = None
    healthy: bool
    error: str | None = None


class PortScanResult(BaseModel):
    host: str
    port: int
    open: bool


class SslCertificateResult(BaseModel):
    hostname: str
    expires: datetime | None = None
    days_remaining: int | None = None
    valid: bool
    error: str | None = None


class DnsResult(BaseModel):
    hostname: str
    addresses: list[str] = Field(default_factory=list)
    resolved: bool
    error: str | None = None


class ServiceHealthResult(BaseModel):
    name: str
    running: bool
    status: str
    pid: int | None = None
    error: str | None = None


class DatabaseHealthResult(BaseModel):
    connected: bool
    latency_ms: float | None = None
    database_type: str = "sqlite"
    error: str | None = None
