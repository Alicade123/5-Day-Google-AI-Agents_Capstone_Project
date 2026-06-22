import pytest

from backend.models.api import MetricsSnapshot
from backend.services.reasoning import ReasoningService


@pytest.fixture
def reasoning():
    from backend.config.settings import Settings

    return ReasoningService(Settings())


def test_reasoning_detects_high_cpu(reasoning):
    snapshot = MetricsSnapshot(
        system={
            "get_cpu_metrics": {"cpu_percent": 96.0},
            "get_memory_metrics": {"percent": 50.0},
            "get_disk_metrics": {"partitions": []},
        },
        tool_count=2,
        success_count=2,
    )
    result = reasoning.analyze_snapshot(snapshot)
    assert any("CPU" in f for f in result.facts)
    assert len(result.anomalies) >= 1
    assert result.agent_response is not None
    assert result.agent_response.confidence.value in ("Low", "Medium", "High")


def test_reasoning_insufficient_evidence(reasoning):
    snapshot = MetricsSnapshot(tool_count=0, success_count=0, failures=["all tools failed"])
    result = reasoning.analyze_snapshot(snapshot)
    assert result.agent_response is not None
    assert result.agent_response.insufficient_evidence is True


def test_reasoning_facts_are_observational(reasoning):
    snapshot = MetricsSnapshot(
        system={"get_memory_metrics": {"percent": 72.5}},
        tool_count=1,
        success_count=1,
    )
    result = reasoning.analyze_snapshot(snapshot)
    assert any("72.5" in f for f in result.facts)
