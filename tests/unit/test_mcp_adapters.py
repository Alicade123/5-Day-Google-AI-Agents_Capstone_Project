"""Unit tests for MCP tool adapters."""

import pytest

from backend.mcp.tool_adapters import (
    MCP_TOOL_NAMES,
    execute_mcp_tool,
    get_mcp_tool_metadata,
    parameters_to_json_schema,
)
from backend.services.tool_registry import ToolParameter, get_tool_registry


def test_mcp_tool_names_match_requirements():
    expected = {
        "get_cpu_metrics",
        "get_memory_metrics",
        "get_disk_metrics",
        "analyze_logs",
        "get_history",
        "get_incidents",
        "check_database",
    }
    assert set(MCP_TOOL_NAMES) == expected


def test_mcp_metadata_includes_schemas():
    metadata = get_mcp_tool_metadata()
    names = {entry["name"] for entry in metadata}
    assert names == set(MCP_TOOL_NAMES)
    for entry in metadata:
        assert entry["description"]
        assert "input_schema" in entry
        if entry["name"] in {"get_cpu_metrics", "check_database"}:
            assert entry.get("response_schema") is not None


def test_parameters_to_json_schema_marks_required_fields():
    schema = parameters_to_json_schema(
        [
            ToolParameter("path", "string", "Log file path", required=True),
            ToolParameter("lines", "integer", "Tail lines", default=500),
        ]
    )
    assert schema["required"] == ["path"]
    assert schema["properties"]["lines"]["default"] == 500


def test_execute_mcp_registry_tool_cpu():
    result = execute_mcp_tool("get_cpu_metrics")
    assert result["success"] is True
    assert result["data"] is not None
    assert "cpu_percent" in result["data"]


def test_execute_mcp_registry_tool_database():
    result = execute_mcp_tool("check_database")
    assert result["success"] is True
    assert "connected" in result["data"]


def test_execute_mcp_history_and_incidents():
    history = execute_mcp_tool("get_history", limit=5)
    assert "records" in history
    assert "total" in history

    incidents = execute_mcp_tool("get_incidents", limit=5)
    assert "incidents" in incidents
    assert "total" in incidents


def test_execute_mcp_unknown_tool():
    result = execute_mcp_tool("nonexistent_tool")
    assert result["success"] is False
    assert "Unknown MCP tool" in (result.get("error") or "")


def test_mcp_metadata_aligns_with_registry():
    registry = get_tool_registry()
    for name in ("get_cpu_metrics", "get_memory_metrics", "get_disk_metrics", "check_database"):
        registry_meta = registry.get(name).metadata()
        mcp_meta = next(m for m in get_mcp_tool_metadata() if m["name"] == name)
        assert mcp_meta["description"] == registry_meta["description"]
        assert mcp_meta["category"] == registry_meta["category"]
