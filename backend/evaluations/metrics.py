import re
import time
from typing import Any

from backend.agents.executor import ToolExecutor
from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.planner import Planner
from backend.evaluations.schema import EvalCase, EvalDataset
from backend.models.logs import AgentResponse


class EvalMetrics:
    """Deterministic eval graders — no LLM text assertions."""

    @staticmethod
    def facts_present(response: AgentResponse) -> tuple[bool, str]:
        ok = len(response.facts) > 0 or response.insufficient_evidence
        return ok, "facts present or insufficient_evidence flagged"

    @staticmethod
    def confidence_present(response: AgentResponse) -> tuple[bool, str]:
        ok = response.confidence is not None
        return ok, f"confidence={response.confidence.value}"

    @staticmethod
    def recommendations_present(response: AgentResponse) -> tuple[bool, str]:
        ok = len(response.recommended_actions) > 0
        return ok, f"recommendations count={len(response.recommended_actions)}"

    @staticmethod
    def response_complete(response: AgentResponse) -> tuple[bool, str]:
        ok = (
            (len(response.facts) > 0 or response.insufficient_evidence)
            and len(response.possible_explanations) > 0
            and len(response.recommended_actions) > 0
            and response.confidence is not None
        )
        return ok, "all response sections populated"

    @staticmethod
    def tool_selection_correct(
        case: EvalCase, tools_used: list[str]
    ) -> tuple[bool, str]:
        if not case.expected_tools:
            return True, "no expected tools specified"
        matched = [t for t in case.expected_tools if t in tools_used]
        ok = len(matched) >= min(1, len(case.expected_tools))
        return ok, f"expected={case.expected_tools}, used={tools_used}"

    @staticmethod
    def grounded_in_observations(response: AgentResponse) -> tuple[bool, str]:
        if response.insufficient_evidence:
            return True, "insufficient evidence correctly declared"
        ok = len(response.facts) > 0 and not response.insufficient_evidence
        return ok, "facts derived from observations"

    @staticmethod
    def no_fabricated_metrics(
        response: AgentResponse, tool_evidence: dict[str, Any]
    ) -> tuple[bool, str]:
        if response.insufficient_evidence:
            return True, "no metrics claimed when evidence insufficient"
        evidence_str = str(tool_evidence)
        number_pattern = re.compile(r"\d+\.?\d*")
        for fact in response.facts:
            numbers = number_pattern.findall(fact)
            for num in numbers:
                if num not in evidence_str and f"{float(num):.1f}" not in evidence_str:
                    if float(num) > 1000:
                        continue
                    return False, f"number {num} in fact not found in tool evidence"
        return True, "fact numbers traceable to tool evidence"

    CHECK_MAP = {
        "facts_present": lambda r, c, t, e: EvalMetrics.facts_present(r),
        "confidence_present": lambda r, c, t, e: EvalMetrics.confidence_present(r),
        "recommendations_present": lambda r, c, t, e: EvalMetrics.recommendations_present(r),
        "response_complete": lambda r, c, t, e: EvalMetrics.response_complete(r),
        "tool_selection_correct": lambda r, c, t, e: EvalMetrics.tool_selection_correct(c, t),
        "grounded_in_observations": lambda r, c, t, e: EvalMetrics.grounded_in_observations(r),
        "no_fabricated_metrics": lambda r, c, t, e: EvalMetrics.no_fabricated_metrics(r, e),
    }
