import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

import structlog

from backend.models import ToolResult

logger = structlog.get_logger(__name__)
T = TypeVar("T")


def run_tool(name: str, fn: Callable[[], T]) -> ToolResult[T]:
    """Execute a tool with timing, logging, and structured error handling."""
    start = time.perf_counter()
    executed_at = datetime.now(UTC)
    try:
        data = fn()
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("tool_executed", tool=name, success=True, duration_ms=round(duration_ms, 2))
        return ToolResult(
            success=True,
            data=data,
            executed_at=executed_at,
            duration_ms=round(duration_ms, 2),
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            "tool_failed",
            tool=name,
            success=False,
            error=str(exc),
            duration_ms=round(duration_ms, 2),
        )
        return ToolResult(
            success=False,
            error=str(exc),
            executed_at=executed_at,
            duration_ms=round(duration_ms, 2),
        )
