import pytest

from backend.services.tool_registry import ToolRegistry, get_tool_registry


def test_registry_has_all_tools():
    registry = get_tool_registry()
    names = {t.name for t in registry.list_all()}
    expected = {
        "get_cpu_metrics",
        "get_memory_metrics",
        "get_disk_metrics",
        "get_network_metrics",
        "get_process_metrics",
        "get_uptime_metrics",
        "check_ping",
        "check_http_health",
        "scan_port",
        "check_ssl_certificate",
        "resolve_dns",
        "check_service_health",
        "check_database",
        "analyze_logs",
    }
    assert expected.issubset(names)


def test_registry_metadata_includes_schema():
    registry = get_tool_registry()
    meta = registry.list_metadata()
    cpu = next(m for m in meta if m["name"] == "get_cpu_metrics")
    assert cpu["description"]
    assert cpu["response_schema"] is not None
    assert "cpu_percent" in str(cpu["response_schema"])


def test_registry_unknown_tool():
    registry = get_tool_registry()
    result = registry.execute("nonexistent_tool")
    assert result.success is False
    assert "Unknown tool" in (result.error or "")


def test_registry_execute_cpu():
    registry = get_tool_registry()
    result = registry.execute("get_cpu_metrics")
    assert result.success is True
    assert result.data is not None
