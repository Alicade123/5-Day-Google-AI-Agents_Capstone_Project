import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import structlog

from backend.agents.planner import ExecutionPlan, ToolInvocation
from backend.models import ToolResult
from backend.services.tool_registry import ToolRegistry, get_tool_registry

logger = structlog.get_logger(__name__)


class ToolExecutor:
    """Executes planned tool invocations with tracing and parallel support."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        max_workers: int = 8,
    ) -> None:
        self._registry = registry or get_tool_registry()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._history: list[dict[str, Any]] = []

    @property
    def execution_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def execute_one(self, invocation: ToolInvocation) -> ToolResult:
        result = self._registry.execute(invocation.tool_name, **invocation.parameters)
        self._history.append(
            {
                "tool": invocation.tool_name,
                "parameters": invocation.parameters,
                "success": result.success,
                "duration_ms": result.duration_ms,
                "error": result.error,
            }
        )
        logger.info(
            "tool_executor_run",
            tool=invocation.tool_name,
            success=result.success,
            duration_ms=result.duration_ms,
        )
        return result

    def execute_plan(self, plan: ExecutionPlan) -> dict[str, ToolResult]:
        results: dict[str, ToolResult] = {}
        for idx, invocation in enumerate(plan.tools):
            key = self._result_key(invocation, idx)
            results[key] = self.execute_one(invocation)
        return results

    async def execute_plan_parallel(self, plan: ExecutionPlan) -> dict[str, ToolResult]:
        loop = asyncio.get_running_loop()

        async def _run(inv: ToolInvocation, idx: int) -> tuple[str, ToolResult]:
            result = await loop.run_in_executor(self._executor, lambda: self.execute_one(inv))
            return self._result_key(inv, idx), result

        pairs = await asyncio.gather(
            *[_run(inv, idx) for idx, inv in enumerate(plan.tools)],
            return_exceptions=True,
        )
        results: dict[str, ToolResult] = {}
        for item in pairs:
            if isinstance(item, Exception):
                logger.warning("executor_parallel_failure", error=str(item))
                continue
            key, result = item
            results[key] = result
        return results

    def _result_key(self, invocation: ToolInvocation, idx: int) -> str:
        if invocation.parameters:
            param_str = "_".join(f"{k}={v}" for k, v in sorted(invocation.parameters.items()))
            return f"{invocation.tool_name}_{param_str}"
        return f"{invocation.tool_name}_{idx}"
