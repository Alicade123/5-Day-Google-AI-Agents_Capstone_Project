from backend.evaluations.metrics import EvalMetrics
from backend.evaluations.schema import EvalCase
from backend.models import ConfidenceLevel
from backend.models.logs import AgentResponse


def test_facts_present_check():
    response = AgentResponse(facts=["CPU is 50%"], confidence=ConfidenceLevel.MEDIUM)
    ok, _ = EvalMetrics.facts_present(response)
    assert ok is True


def test_insufficient_evidence_passes_facts_check():
    response = AgentResponse(insufficient_evidence=True)
    ok, _ = EvalMetrics.facts_present(response)
    assert ok is True


def test_tool_selection_correct():
    case = EvalCase(id="t1", query="db?", expected_tools=["check_database"])
    ok, _ = EvalMetrics.tool_selection_correct(case, ["check_database", "get_cpu_metrics"])
    assert ok is True


def test_tool_selection_fails():
    case = EvalCase(id="t2", query="db?", expected_tools=["check_database"])
    ok, _ = EvalMetrics.tool_selection_correct(case, ["get_cpu_metrics"])
    assert ok is False


def test_no_fabricated_metrics_passes():
    response = AgentResponse(facts=["CPU utilization is 50.0%"])
    evidence = {"get_cpu_metrics": {"cpu_percent": 50.0}}
    ok, _ = EvalMetrics.no_fabricated_metrics(response, evidence)
    assert ok is True


def test_response_complete():
    response = AgentResponse(
        facts=["test"],
        possible_explanations=["exp"],
        recommended_actions=["act"],
        confidence=ConfidenceLevel.HIGH,
    )
    ok, _ = EvalMetrics.response_complete(response)
    assert ok is True
