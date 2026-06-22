"""ADK-compatible monitoring tool wrappers.

These functions are registered with the Google ADK root agent.
All return deterministic data from the underlying tool layer.
"""

from backend.tools import (
    analyze_logs,
    check_database,
    check_http_health,
    check_ping,
    get_cpu_metrics,
    get_disk_metrics,
    get_memory_metrics,
    get_process_metrics,
    get_uptime_metrics,
)


def adk_get_cpu_metrics() -> dict:
    """Returns current CPU utilization percentage and load averages."""
    result = get_cpu_metrics()
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "CPU metrics unavailable"}


def adk_get_memory_metrics() -> dict:
    """Returns memory usage: used, available, total bytes and percent."""
    result = get_memory_metrics()
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "Memory metrics unavailable"}


def adk_get_disk_metrics() -> dict:
    """Returns disk usage per partition."""
    result = get_disk_metrics()
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "Disk metrics unavailable"}


def adk_get_process_metrics(limit: int = 10) -> dict:
    """Returns top processes by CPU and memory consumption."""
    result = get_process_metrics(limit=limit)
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "Process metrics unavailable"}


def adk_get_uptime_metrics() -> dict:
    """Returns system uptime and boot time."""
    result = get_uptime_metrics()
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "Uptime metrics unavailable"}


def adk_check_ping(host: str) -> dict:
    """Checks if a host is reachable and returns latency in milliseconds."""
    result = check_ping(host)
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "Ping check failed"}


def adk_check_http_health(url: str) -> dict:
    """Checks HTTP endpoint health, status code, and response time."""
    result = check_http_health(url)
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "HTTP health check failed"}


def adk_check_database() -> dict:
    """Checks database connectivity and query latency."""
    result = check_database()
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "Database check failed"}


def adk_analyze_logs(path: str, lines: int = 500) -> dict:
    """Analyzes a log file for errors and recurring patterns."""
    result = analyze_logs(path, lines=lines)
    if result.success and result.data:
        return result.data.model_dump(mode="json")
    return {"error": result.error or "Log analysis failed"}


MONITORING_TOOLS = [
    adk_get_cpu_metrics,
    adk_get_memory_metrics,
    adk_get_disk_metrics,
    adk_get_process_metrics,
    adk_get_uptime_metrics,
    adk_check_ping,
    adk_check_http_health,
    adk_check_database,
    adk_analyze_logs,
]
