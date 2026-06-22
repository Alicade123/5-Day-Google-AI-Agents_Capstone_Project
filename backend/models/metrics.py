from datetime import datetime

from pydantic import BaseModel, Field


class CpuMetrics(BaseModel):
    cpu_percent: float
    per_cpu_percent: list[float] = Field(default_factory=list)
    load_average: list[float] = Field(default_factory=list)


class MemoryMetrics(BaseModel):
    used_bytes: int
    available_bytes: int
    total_bytes: int
    percent: float


class DiskPartition(BaseModel):
    device: str
    mountpoint: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


class DiskMetrics(BaseModel):
    partitions: list[DiskPartition] = Field(default_factory=list)


class NetworkMetrics(BaseModel):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    active_connections: int


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


class ProcessMetrics(BaseModel):
    processes: list[ProcessInfo] = Field(default_factory=list)


class UptimeMetrics(BaseModel):
    uptime_seconds: float
    boot_time: datetime
    load_average: list[float] = Field(default_factory=list)
