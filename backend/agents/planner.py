from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolInvocation:
    tool_name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    query: str
    intent: str
    tools: list[ToolInvocation] = field(default_factory=list)


class Planner:
    """Selects monitoring tools based on user intent using keyword rules."""

    INTENT_KEYWORDS: dict[str, list[str]] = {
        "performance": ["performance", "slow", "degrading", "lag", "latency", "cpu"],
        "memory": ["memory", "ram", "oom", "out of memory"],
        "disk": ["disk", "storage", "space", "full"],
        "network": ["network", "connectivity", "ping", "dns"],
        "logs": ["log", "error", "exception", "crash", "failure"],
        "database": ["database", "db", "sql", "connection pool"],
        "services": ["service", "process", "port", "http", "endpoint", "ssl"],
        "health": ["health", "status", "monitor", "check", "overall"],
    }

    TOOL_MAP: dict[str, list[ToolInvocation]] = {
        "performance": [
            ToolInvocation("get_cpu_metrics"),
            ToolInvocation("get_memory_metrics"),
            ToolInvocation("get_process_metrics", {"limit": 10}),
            ToolInvocation("get_disk_metrics"),
            ToolInvocation("get_uptime_metrics"),
        ],
        "memory": [
            ToolInvocation("get_memory_metrics"),
            ToolInvocation("get_process_metrics", {"limit": 10}),
        ],
        "disk": [ToolInvocation("get_disk_metrics")],
        "network": [
            ToolInvocation("get_network_metrics"),
            ToolInvocation("check_ping", {"host": "8.8.8.8"}),
        ],
        "logs": [],  # filled dynamically from settings
        "database": [ToolInvocation("check_database")],
        "services": [
            ToolInvocation("check_database"),
        ],
        "health": [
            ToolInvocation("get_cpu_metrics"),
            ToolInvocation("get_memory_metrics"),
            ToolInvocation("get_disk_metrics"),
            ToolInvocation("get_network_metrics"),
            ToolInvocation("get_process_metrics", {"limit": 5}),
            ToolInvocation("get_uptime_metrics"),
            ToolInvocation("check_database"),
        ],
    }

    def __init__(self, log_paths: list[str] | None = None, http_urls: list[str] | None = None,
                 ping_hosts: list[str] | None = None, ports: list[int] | None = None,
                 services: list[str] | None = None) -> None:
        self._log_paths = log_paths or []
        self._http_urls = http_urls or []
        self._ping_hosts = ping_hosts or []
        self._ports = ports or []
        self._services = services or []

    def plan(self, query: str) -> ExecutionPlan:
        query_lower = query.lower()
        intent = self._classify_intent(query_lower)
        tools = list(self.TOOL_MAP.get(intent, self.TOOL_MAP["health"]))

        if intent in ("logs", "performance", "health") or any(
            kw in query_lower for kw in self.INTENT_KEYWORDS["logs"]
        ):
            tools.extend(
                ToolInvocation("analyze_logs", {"path": path, "lines": 500})
                for path in self._log_paths
            )
        if intent in ("services", "performance", "health", "network"):
            tools.extend(
                ToolInvocation("check_http_health", {"url": url}) for url in self._http_urls
            )
            tools.extend(
                ToolInvocation("check_ping", {"host": host}) for host in self._ping_hosts
            )
            tools.extend(
                ToolInvocation("scan_port", {"host": "localhost", "port": port})
                for port in self._ports
            )
            tools.extend(
                ToolInvocation("check_service_health", {"service_name": svc})
                for svc in self._services
            )

        # Deduplicate by tool name + params
        seen: set[tuple[str, str]] = set()
        unique: list[ToolInvocation] = []
        for inv in tools:
            key = (inv.tool_name, str(sorted(inv.parameters.items())))
            if key not in seen:
                seen.add(key)
                unique.append(inv)

        return ExecutionPlan(query=query, intent=intent, tools=unique)

    def _classify_intent(self, query_lower: str) -> str:
        scores: dict[str, int] = {intent: 0 for intent in self.INTENT_KEYWORDS}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    scores[intent] += 1
        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] > 0 else "health"
