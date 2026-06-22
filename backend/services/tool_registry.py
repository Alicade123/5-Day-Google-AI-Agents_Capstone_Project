from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from backend.models import ToolResult


@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., ToolResult]
    parameters: list[ToolParameter] = field(default_factory=list)
    response_schema: type[BaseModel] | None = None
    category: str = "general"

    def execute(self, **kwargs: Any) -> ToolResult:
        if self.parameters:
            allowed = {p.name for p in self.parameters}
            filtered = {k: v for k, v in kwargs.items() if k in allowed}
            required = [p.name for p in self.parameters if p.required]
            missing = [name for name in required if name not in filtered]
            if missing:
                return ToolResult(success=False, error=f"Missing required parameters: {missing}")
            return self.handler(**filtered)
        return self.handler(**kwargs) if kwargs else self.handler()

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                }
                for p in self.parameters
            ],
            "response_schema": (
                self.response_schema.model_json_schema() if self.response_schema else None
            ),
        }


class ToolRegistry:
    """Central registry for monitoring tools with metadata for discovery and execution."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_all(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def list_metadata(self) -> list[dict[str, Any]]:
        return [tool.metadata() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        return tool.execute(**kwargs)

    def register_many(self, tools: list[ToolDefinition]) -> None:
        for tool in tools:
            self.register(tool)


def _build_default_registry() -> ToolRegistry:
    from backend.models.health import (
        DatabaseHealthResult,
        DnsResult,
        HttpHealthResult,
        PingResult,
        PortScanResult,
        ServiceHealthResult,
        SslCertificateResult,
    )
    from backend.models.logs import LogAnalysisResult
    from backend.models.metrics import (
        CpuMetrics,
        DiskMetrics,
        MemoryMetrics,
        NetworkMetrics,
        ProcessMetrics,
        UptimeMetrics,
    )
    from backend.tools import (
        analyze_logs,
        check_database,
        check_http_health,
        check_ping,
        check_service_health,
        check_ssl_certificate,
        get_cpu_metrics,
        get_disk_metrics,
        get_memory_metrics,
        get_network_metrics,
        get_process_metrics,
        get_uptime_metrics,
        resolve_dns,
        scan_port,
    )

    registry = ToolRegistry()
    registry.register_many(
        [
            ToolDefinition(
                name="get_cpu_metrics",
                description="Returns current CPU utilization and load averages.",
                handler=get_cpu_metrics,
                response_schema=CpuMetrics,
                category="system",
            ),
            ToolDefinition(
                name="get_memory_metrics",
                description="Returns memory usage statistics.",
                handler=get_memory_metrics,
                response_schema=MemoryMetrics,
                category="system",
            ),
            ToolDefinition(
                name="get_disk_metrics",
                description="Returns disk usage per partition.",
                handler=get_disk_metrics,
                response_schema=DiskMetrics,
                category="system",
            ),
            ToolDefinition(
                name="get_network_metrics",
                description="Returns network I/O counters and active connections.",
                handler=get_network_metrics,
                response_schema=NetworkMetrics,
                category="system",
            ),
            ToolDefinition(
                name="get_process_metrics",
                description="Returns top processes by CPU and memory consumption.",
                handler=get_process_metrics,
                parameters=[
                    ToolParameter("limit", "integer", "Max processes to return", default=10),
                ],
                response_schema=ProcessMetrics,
                category="system",
            ),
            ToolDefinition(
                name="get_uptime_metrics",
                description="Returns system uptime and boot time.",
                handler=get_uptime_metrics,
                response_schema=UptimeMetrics,
                category="system",
            ),
            ToolDefinition(
                name="check_ping",
                description="Checks host reachability and latency.",
                handler=check_ping,
                parameters=[
                    ToolParameter("host", "string", "Target hostname or IP", required=True),
                ],
                response_schema=PingResult,
                category="infrastructure",
            ),
            ToolDefinition(
                name="check_http_health",
                description="Checks HTTP endpoint health and response time.",
                handler=check_http_health,
                parameters=[
                    ToolParameter("url", "string", "HTTP URL to check", required=True),
                ],
                response_schema=HttpHealthResult,
                category="infrastructure",
            ),
            ToolDefinition(
                name="scan_port",
                description="Checks if a TCP port is open on a host.",
                handler=scan_port,
                parameters=[
                    ToolParameter("host", "string", "Target host", required=True),
                    ToolParameter("port", "integer", "TCP port number", required=True),
                ],
                response_schema=PortScanResult,
                category="infrastructure",
            ),
            ToolDefinition(
                name="check_ssl_certificate",
                description="Checks SSL certificate validity and expiry.",
                handler=check_ssl_certificate,
                parameters=[
                    ToolParameter("hostname", "string", "Hostname to check", required=True),
                    ToolParameter("port", "integer", "TLS port", default=443),
                ],
                response_schema=SslCertificateResult,
                category="infrastructure",
            ),
            ToolDefinition(
                name="resolve_dns",
                description="Resolves a hostname to IP addresses.",
                handler=resolve_dns,
                parameters=[
                    ToolParameter("hostname", "string", "Hostname to resolve", required=True),
                ],
                response_schema=DnsResult,
                category="infrastructure",
            ),
            ToolDefinition(
                name="check_service_health",
                description="Checks if a named process/service is running.",
                handler=check_service_health,
                parameters=[
                    ToolParameter("service_name", "string", "Service or process name", required=True),
                ],
                response_schema=ServiceHealthResult,
                category="services",
            ),
            ToolDefinition(
                name="check_database",
                description="Checks database connectivity and latency.",
                handler=check_database,
                response_schema=DatabaseHealthResult,
                category="services",
            ),
            ToolDefinition(
                name="analyze_logs",
                description="Analyzes log files for errors and recurring patterns.",
                handler=analyze_logs,
                parameters=[
                    ToolParameter("path", "string", "Path to log file", required=True),
                    ToolParameter("lines", "integer", "Number of tail lines", default=500),
                ],
                response_schema=LogAnalysisResult,
                category="logs",
            ),
        ]
    )
    return registry


_default_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = _build_default_registry()
    return _default_registry
