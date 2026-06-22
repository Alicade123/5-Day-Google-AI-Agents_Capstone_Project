import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

import structlog

from backend.config.settings import Settings, get_settings
from backend.models.api import MetricsSnapshot
from backend.models import ToolResult
from backend.services.tool_registry import ToolRegistry, get_tool_registry

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Aggregates monitoring tool results with parallel execution and graceful failure handling."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        settings: Settings | None = None,
        max_workers: int = 8,
    ) -> None:
        self._registry = registry or get_tool_registry()
        self._settings = settings or get_settings()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def _run_tool(self, name: str, **kwargs: Any) -> tuple[str, ToolResult]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            self._executor,
            lambda: self._registry.execute(name, **kwargs),
        )
        return name, result

    async def _run_parallel(self, tasks: list[tuple[str, dict[str, Any]]]) -> dict[str, ToolResult]:
        if not tasks:
            return {}
        results = await asyncio.gather(
            *[self._run_tool(name, **kwargs) for name, kwargs in tasks],
            return_exceptions=True,
        )
        output: dict[str, ToolResult] = {}
        for item in results:
            if isinstance(item, Exception):
                logger.warning("tool_parallel_failure", error=str(item))
                continue
            name, tool_result = item
            output[name] = tool_result
        return output

    def _normalize_result(self, result: ToolResult) -> dict[str, Any]:
        if result.success and result.data is not None:
            if hasattr(result.data, "model_dump"):
                return result.data.model_dump(mode="json")
            return {"value": result.data}
        return {"error": result.error or "unknown error"}

    def _build_snapshot(
        self,
        system: dict[str, ToolResult],
        infrastructure: dict[str, ToolResult],
        services: dict[str, ToolResult],
        logs: dict[str, ToolResult],
    ) -> MetricsSnapshot:
        failures: list[str] = []
        all_results = {**system, **infrastructure, **services, **logs}
        success_count = 0

        for name, result in all_results.items():
            if result.success:
                success_count += 1
            else:
                failures.append(f"{name}: {result.error}")

        def normalize_group(group: dict[str, ToolResult]) -> dict[str, Any]:
            return {name: self._normalize_result(r) for name, r in group.items()}

        return MetricsSnapshot(
            collected_at=datetime.now(UTC),
            system=normalize_group(system),
            infrastructure=normalize_group(infrastructure),
            services=normalize_group(services),
            logs=normalize_group(logs),
            failures=failures,
            tool_count=len(all_results),
            success_count=success_count,
        )

    def _system_tasks(self) -> list[tuple[str, dict[str, Any]]]:
        return [
            ("get_cpu_metrics", {}),
            ("get_memory_metrics", {}),
            ("get_disk_metrics", {}),
            ("get_network_metrics", {}),
            ("get_process_metrics", {"limit": 10}),
            ("get_uptime_metrics", {}),
        ]

    def _infrastructure_tasks(self) -> list[tuple[str, dict[str, Any]]]:
        tasks: list[tuple[str, dict[str, Any]]] = []
        for host in self._settings.csv_list(self._settings.ping_hosts):
            tasks.append(("check_ping", {"host": host}))
        for url in self._settings.csv_list(self._settings.http_health_urls):
            tasks.append(("check_http_health", {"url": url}))
        for port_str in self._settings.csv_list(self._settings.monitored_ports):
            try:
                port = int(port_str)
                tasks.append(("scan_port", {"host": "localhost", "port": port}))
            except ValueError:
                continue
        return tasks

    def _service_tasks(self) -> list[tuple[str, dict[str, Any]]]:
        tasks: list[tuple[str, dict[str, Any]]] = [("check_database", {})]
        for service in self._settings.csv_list(self._settings.monitored_services):
            tasks.append(("check_service_health", {"service_name": service}))
        return tasks

    def _log_tasks(self) -> list[tuple[str, dict[str, Any]]]:
        return [
            ("analyze_logs", {"path": path, "lines": 500})
            for path in self._settings.csv_list(self._settings.log_paths)
        ]

    async def collect_system_metrics(self) -> dict[str, ToolResult]:
        return await self._run_parallel(self._system_tasks())

    async def collect_infrastructure_checks(self) -> dict[str, ToolResult]:
        return await self._run_parallel(self._infrastructure_tasks())

    async def collect_service_checks(self) -> dict[str, ToolResult]:
        return await self._run_parallel(self._service_tasks())

    async def collect_logs(self) -> dict[str, ToolResult]:
        return await self._run_parallel(self._log_tasks())

    async def collect_full_snapshot(self) -> MetricsSnapshot:
        system, infrastructure, services, logs = await asyncio.gather(
            self.collect_system_metrics(),
            self.collect_infrastructure_checks(),
            self.collect_service_checks(),
            self.collect_logs(),
        )
        snapshot = self._build_snapshot(system, infrastructure, services, logs)
        logger.info(
            "metrics_collected",
            tool_count=snapshot.tool_count,
            success_count=snapshot.success_count,
            failure_count=len(snapshot.failures),
        )
        return snapshot
