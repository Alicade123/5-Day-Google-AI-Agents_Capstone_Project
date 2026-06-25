"""MCP server exposing server health monitoring tools over stdio transport."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from backend.mcp.tool_adapters import execute_mcp_tool, get_mcp_tool_metadata

mcp = FastMCP(
    name="server-health-agent",
    instructions=(
        "Deterministic server health monitoring tools. "
        "All metrics come from real tool execution — never fabricate values."
    ),
)


def _registry_description(name: str, fallback: str) -> str:
    for entry in get_mcp_tool_metadata():
        if entry["name"] == name:
            return entry["description"]
    return fallback


@mcp.tool(name="get_cpu_metrics", description=_registry_description("get_cpu_metrics", ""))
def mcp_get_cpu_metrics() -> dict:
    """Returns current CPU utilization and load averages."""
    return execute_mcp_tool("get_cpu_metrics")


@mcp.tool(name="get_memory_metrics", description=_registry_description("get_memory_metrics", ""))
def mcp_get_memory_metrics() -> dict:
    """Returns memory usage statistics."""
    return execute_mcp_tool("get_memory_metrics")


@mcp.tool(name="get_disk_metrics", description=_registry_description("get_disk_metrics", ""))
def mcp_get_disk_metrics() -> dict:
    """Returns disk usage per partition."""
    return execute_mcp_tool("get_disk_metrics")


@mcp.tool(name="analyze_logs", description=_registry_description("analyze_logs", ""))
def mcp_analyze_logs(path: str, lines: int = 500) -> dict:
    """Analyzes log files for errors and recurring patterns."""
    return execute_mcp_tool("analyze_logs", path=path, lines=lines)


@mcp.tool(name="get_history", description=_registry_description("get_history", ""))
def mcp_get_history(limit: int = 100, since_minutes: int | None = None) -> dict:
    """Returns persisted metric snapshot history."""
    return execute_mcp_tool("get_history", limit=limit, since_minutes=since_minutes)


@mcp.tool(name="get_incidents", description=_registry_description("get_incidents", ""))
def mcp_get_incidents(limit: int = 50) -> dict:
    """Returns historical incidents recorded by the agent."""
    return execute_mcp_tool("get_incidents", limit=limit)


@mcp.tool(name="check_database", description=_registry_description("check_database", ""))
def mcp_check_database() -> dict:
    """Checks database connectivity and latency."""
    return execute_mcp_tool("check_database")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
