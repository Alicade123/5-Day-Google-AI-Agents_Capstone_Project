"""MCP server integration for exposing monitoring tools to external agents."""

from backend.mcp.tool_adapters import MCP_TOOL_NAMES, execute_mcp_tool, get_mcp_tool_metadata

__all__ = ["MCP_TOOL_NAMES", "execute_mcp_tool", "get_mcp_tool_metadata"]
