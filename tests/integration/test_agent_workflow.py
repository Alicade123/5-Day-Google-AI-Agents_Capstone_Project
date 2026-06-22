import pytest

from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.planner import Planner
from backend.agents.executor import ToolExecutor


@pytest.mark.asyncio
async def test_orchestrator_query_returns_structured_response():
    orchestrator = AgentOrchestrator()
    response = await orchestrator.query("What is the current CPU and memory usage?")
    assert isinstance(response.facts, list)
    assert isinstance(response.possible_explanations, list)
    assert response.confidence.value in ("Low", "Medium", "High")
    assert isinstance(response.recommended_actions, list)


@pytest.mark.asyncio
async def test_orchestrator_analyze_full():
    orchestrator = AgentOrchestrator()
    result = await orchestrator.analyze_full()
    assert result.snapshot.tool_count > 0
    assert result.agent_response is not None


@pytest.mark.asyncio
async def test_executor_parallel_plan():
    planner = Planner()
    executor = ToolExecutor()
    plan = planner.plan("Check CPU and memory")
    results = await executor.execute_plan_parallel(plan)
    assert len(results) == len(plan.tools)
    assert len(executor.execution_history) == len(plan.tools)
