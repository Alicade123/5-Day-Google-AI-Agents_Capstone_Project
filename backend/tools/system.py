import platform
from datetime import datetime

import psutil

from backend.models.metrics import (
    CpuMetrics,
    DiskMetrics,
    DiskPartition,
    MemoryMetrics,
    NetworkMetrics,
    ProcessInfo,
    ProcessMetrics,
    UptimeMetrics,
)
from backend.models import ToolResult
from backend.tools.base import run_tool


def get_cpu_metrics() -> ToolResult[CpuMetrics]:
    def _collect() -> CpuMetrics:
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        load_avg: list[float] = []
        if hasattr(psutil, "getloadavg"):
            try:
                load_avg = list(psutil.getloadavg())
            except OSError:
                load_avg = []
        return CpuMetrics(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            per_cpu_percent=per_cpu,
            load_average=load_avg,
        )

    return run_tool("get_cpu_metrics", _collect)


def get_memory_metrics() -> ToolResult[MemoryMetrics]:
    def _collect() -> MemoryMetrics:
        mem = psutil.virtual_memory()
        return MemoryMetrics(
            used_bytes=mem.used,
            available_bytes=mem.available,
            total_bytes=mem.total,
            percent=mem.percent,
        )

    return run_tool("get_memory_metrics", _collect)


def get_disk_metrics() -> ToolResult[DiskMetrics]:
    def _collect() -> DiskMetrics:
        partitions: list[DiskPartition] = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError):
                continue
            partitions.append(
                DiskPartition(
                    device=part.device,
                    mountpoint=part.mountpoint,
                    total_bytes=usage.total,
                    used_bytes=usage.used,
                    free_bytes=usage.free,
                    percent=usage.percent,
                )
            )
        return DiskMetrics(partitions=partitions)

    return run_tool("get_disk_metrics", _collect)


def get_network_metrics() -> ToolResult[NetworkMetrics]:
    def _collect() -> NetworkMetrics:
        net = psutil.net_io_counters()
        connections = 0
        try:
            connections = len(psutil.net_connections(kind="inet"))
        except (psutil.AccessDenied, PermissionError):
            connections = -1
        return NetworkMetrics(
            bytes_sent=net.bytes_sent,
            bytes_recv=net.bytes_recv,
            packets_sent=net.packets_sent,
            packets_recv=net.packets_recv,
            active_connections=connections,
        )

    return run_tool("get_network_metrics", _collect)


def get_process_metrics(limit: int = 10) -> ToolResult[ProcessMetrics]:
    def _collect() -> ProcessMetrics:
        processes: list[ProcessInfo] = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                processes.append(
                    ProcessInfo(
                        pid=info["pid"],
                        name=info["name"] or "unknown",
                        cpu_percent=info.get("cpu_percent") or 0.0,
                        memory_percent=info.get("memory_percent") or 0.0,
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda p: (p.cpu_percent, p.memory_percent), reverse=True)
        return ProcessMetrics(processes=processes[:limit])

    return run_tool("get_process_metrics", _collect)


def get_uptime_metrics() -> ToolResult[UptimeMetrics]:
    def _collect() -> UptimeMetrics:
        boot = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = (datetime.now() - boot).total_seconds()
        load_avg: list[float] = []
        if hasattr(psutil, "getloadavg") and platform.system() != "Windows":
            try:
                load_avg = list(psutil.getloadavg())
            except OSError:
                load_avg = []
        return UptimeMetrics(
            uptime_seconds=uptime_seconds,
            boot_time=boot,
            load_average=load_avg,
        )

    return run_tool("get_uptime_metrics", _collect)
