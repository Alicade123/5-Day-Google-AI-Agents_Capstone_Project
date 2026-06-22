from backend.models import ConfidenceLevel
from backend.models.api import AnalysisResult
from backend.models.logs import AgentResponse


class ResponseGenerator:
    """Produces structured agent responses from analysis results."""

    def generate(self, analysis: AnalysisResult) -> AgentResponse:
        if analysis.agent_response:
            return analysis.agent_response
        return AgentResponse(
            facts=analysis.facts,
            possible_explanations=analysis.possible_explanations,
            confidence=ConfidenceLevel.MEDIUM,
            recommended_actions=analysis.recommended_actions,
            anomalies=analysis.anomalies,
            insufficient_evidence=analysis.snapshot.success_count == 0,
        )

    def format_text(self, response: AgentResponse) -> str:
        if response.insufficient_evidence:
            return "I could not obtain sufficient evidence."

        sections = [
            "Facts:",
            *[f"- {fact}" for fact in response.facts],
            "",
            "Possible explanations:",
            *[f"- {exp}" for exp in response.possible_explanations],
            "",
            f"Confidence: {response.confidence.value}",
            "",
            "Recommended actions:",
            *[f"- {action}" for action in response.recommended_actions],
        ]
        return "\n".join(sections)
