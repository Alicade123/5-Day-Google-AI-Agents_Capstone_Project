"""Adapters bridging the tool registry and services to MCP tool contracts."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.config.settings import get_settings
from backend.memory.long_term import SQLiteLongTermMemory
from backend.models import ToolResult
from backend.services.history import HistoryService
from backend.services.tool_registry import ToolParameter, ToolRegistry, get_tool_registry

MCP_TOOL_NAMES: list[str] = [
    "get_cpu_metrics",
    "get_memory_metrics",
    "get_disk_metrics",
    "analyze_logs",
    "get_history",
    "get_incidents",
    "check_database",
]

_REGISTRY_TOOLS = frozenset(
    {
        "get_cpu_metrics",
        "get_memory_metrics",
        "get_disk_metrics",
        "analyze_logs",
        "check_database",
    }
)

_HISTORY_TOOL_METADATA: dict[str, Any] = {
    "name": "get_history",
    "description": "Returns persisted metric snapshot history with optional time window.",
    "category": "history",
    "parameters": [
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum number of records to return",
            "required": False,
            "default": 100,
        },
        {
            "name": "since_minutes",
            "type": "integer",
            "description": "Only include records from the last N minutes",
            "required": False,
            "default": None,
        },
    ],
    "response_schema": {
        "type": "object",
        "properties": {
            "records": {"type": "array"},
            "total": {"type": "integer"},
        },
    },
}

_INCIDENTS_TOOL_METADATA: dict[str, Any] = {
    "name": "get_incidents",
    "description": "Returns historical incidents recorded by the agent.",
    "category": "incidents",
    "parameters": [
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum number of incidents to return",
            "required": False,
            "default": 50,
        },
    ],
    "response_schema": {
        "type": "object",
        "properties": {
            "incidents": {"type": "array"},
            "total": {"type": "integer"},
        },
    },
}


def _db_path() -> str:
    return get_settings().database_url.replace("sqlite+aiosqlite:///", "")


def parameters_to_json_schema(parameters: list[ToolParameter]) -> dict[str, Any]:
    """Convert registry parameters to JSON Schema for MCP tool input."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    for param in parameters:
        json_type = {
            "string": "string",
            "integer": "integer",
            "number": "number",
            "boolean": "boolean",
        }.get(param.type, "string")
        prop: dict[str, Any] = {"type": json_type, "description": param.description}
        if param.default is not None:
            prop["default"] = param.default
        properties[param.name] = prop
        if param.required:
            required.append(param.name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def serialize_tool_result(result: ToolResult) -> dict[str, Any]:
    """Serialize ToolResult to a deterministic JSON-friendly dict."""
    return result.model_dump(mode="json")


def get_mcp_tool_metadata(registry: ToolRegistry | None = None) -> list[dict[str, Any]]:
    """Return MCP-exposed tool metadata aligned with the tool registry."""
    reg = registry or get_tool_registry()
    metadata: list[dict[str, Any]] = []
    for name in MCP_TOOL_NAMES:
        if name in _REGISTRY_TOOLS:
            tool = reg.get(name)
            if tool is None:
                continue
            entry = tool.metadata()
            entry["input_schema"] = parameters_to_json_schema(tool.parameters)
            metadata.append(entry)
        elif name == "get_history":
            entry = dict(_HISTORY_TOOL_METADATA)
            entry["input_schema"] = parameters_to_json_schema(
                [
                    ToolParameter("limit", "integer", "Maximum records", default=100),
                    ToolParameter(
                        "since_minutes",
                        "integer",
                        "Only include records from the last N minutes",
                        default=None,
                    ),
                ]
            )
            metadata.append(entry)
        elif name == "get_incidents":
            entry = dict(_INCIDENTS_TOOL_METADATA)
            entry["input_schema"] = parameters_to_json_schema(
                [ToolParameter("limit", "integer", "Maximum incidents", default=50)]
            )
            metadata.append(entry)
    return metadata


async def _fetch_history(limit: int = 100, since_minutes: int | None = None) -> dict[str, Any]:
    history = HistoryService(db_path=_db_path())
    await history.initialize()
    response = await history.get_history(limit=limit, since_minutes=since_minutes)
    return response.model_dump(mode="json")


async def _fetch_incidents(limit: int = 50) -> dict[str, Any]:
    memory = SQLiteLongTermMemory(db_path=_db_path())
    await memory.initialize()
    incidents = await memory.list_incidents(limit=limit)
    payload = [incident.model_dump(mode="json") for incident in incidents]
    return {"incidents": payload, "total": len(payload)}


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


def execute_mcp_tool(name: str, **kwargs: Any) -> dict[str, Any]:
    """Execute an MCP-exposed tool via registry or service adapters."""
    if name not in MCP_TOOL_NAMES:
        return serialize_tool_result(
            ToolResult(success=False, error=f"Unknown MCP tool: {name}")
        )

    if name in _REGISTRY_TOOLS:
        registry = get_tool_registry()
        return serialize_tool_result(registry.execute(name, **kwargs))

    if name == "get_history":
        limit = int(kwargs.get("limit", 100))
        since_raw = kwargs.get("since_minutes")
        since_minutes = int(since_raw) if since_raw is not None else None
        return _run_async(_fetch_history(limit=limit, since_minutes=since_minutes))

    if name == "get_incidents":
        limit = int(kwargs.get("limit", 50))
        return _run_async(_fetch_incidents(limit=limit))

    return serialize_tool_result(ToolResult(success=False, error=f"Unhandled MCP tool: {name}"))
