import sqlite3
import time

import psutil

from backend.config.settings import get_settings
from backend.models.health import DatabaseHealthResult, ServiceHealthResult
from backend.models import ToolResult
from backend.tools.base import run_tool


def check_service_health(service_name: str) -> ToolResult[ServiceHealthResult]:
    def _collect() -> ServiceHealthResult:
        for proc in psutil.process_iter(["pid", "name", "status"]):
            try:
                info = proc.info
                name = (info.get("name") or "").lower()
                if service_name.lower() in name:
                    return ServiceHealthResult(
                        name=service_name,
                        running=True,
                        status=info.get("status") or "running",
                        pid=info.get("pid"),
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return ServiceHealthResult(
            name=service_name,
            running=False,
            status="not_found",
            error=f"No process matching '{service_name}' found",
        )

    return run_tool("check_service_health", _collect)


def check_database() -> ToolResult[DatabaseHealthResult]:
    def _collect() -> DatabaseHealthResult:
        settings = get_settings()
        db_url = settings.database_check_url
        if not db_url.startswith("sqlite"):
            return DatabaseHealthResult(
                connected=False,
                database_type="unknown",
                error="Only sqlite checks are supported in this version",
            )
        path = db_url.replace("sqlite:///", "").split("?")[0]
        start = time.perf_counter()
        try:
            conn = sqlite3.connect(path, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            latency = round((time.perf_counter() - start) * 1000, 2)
            return DatabaseHealthResult(connected=True, latency_ms=latency, database_type="sqlite")
        except sqlite3.Error as exc:
            return DatabaseHealthResult(
                connected=False,
                database_type="sqlite",
                error=str(exc),
            )

    return run_tool("check_database", _collect)
