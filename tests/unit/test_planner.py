import pytest

from backend.agents.planner import Planner


@pytest.fixture
def planner():
    return Planner(
        log_paths=["/var/log/app.log"],
        http_urls=["http://localhost/health"],
        ping_hosts=["8.8.8.8"],
        ports=[443],
        services=["nginx"],
    )


def test_planner_performance_intent(planner):
    plan = planner.plan("Why is server performance degrading?")
    assert plan.intent == "performance"
    tool_names = {t.tool_name for t in plan.tools}
    assert "get_cpu_metrics" in tool_names
    assert "get_memory_metrics" in tool_names


def test_planner_log_intent(planner):
    plan = planner.plan("Show me recent errors in the logs")
    assert plan.intent == "logs"
    assert any(t.tool_name == "analyze_logs" for t in plan.tools)


def test_planner_database_intent(planner):
    plan = planner.plan("Is the database connection healthy?")
    assert plan.intent == "database"
    assert any(t.tool_name == "check_database" for t in plan.tools)


def test_planner_deduplicates_tools(planner):
    plan = planner.plan("Check overall server health status")
    names = [t.tool_name for t in plan.tools]
    assert len(names) == len(set(names))
