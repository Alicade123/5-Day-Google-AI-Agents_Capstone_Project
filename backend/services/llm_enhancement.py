import structlog

from backend.config.settings import get_settings
from backend.models.logs import AgentResponse

logger = structlog.get_logger(__name__)


class LLMEnhancementService:
    """Refines explanation wording only — never generates metrics, facts, or confidence."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def is_available(self) -> bool:
        return bool(self._settings.google_api_key)

    async def enhance_explanations(self, response: AgentResponse) -> AgentResponse:
        if not self.is_available or response.insufficient_evidence:
            return response

        try:
            from google import genai

            client = genai.Client(api_key=self._settings.google_api_key)
            facts_block = "\n".join(f"- {f}" for f in response.facts)
            prompt = (
                "You are a server monitoring assistant. Given ONLY these observed facts, "
                "rewrite the possible explanations to be clearer and more actionable. "
                "Do NOT add new metrics, numbers, or facts. Do NOT change confidence level.\n\n"
                f"Facts:\n{facts_block}\n\n"
                f"Current explanations:\n"
                + "\n".join(f"- {e}" for e in response.possible_explanations)
                + "\n\nReturn only a bullet list of improved explanations, one per line."
            )
            result = client.models.generate_content(
                model=self._settings.agent_model,
                contents=prompt,
            )
            text = result.text or ""
            refined = [
                line.lstrip("- ").strip()
                for line in text.strip().split("\n")
                if line.strip() and not line.startswith("#")
            ]
            if refined:
                response.possible_explanations = refined
                logger.info("llm_explanations_enhanced", count=len(refined))
        except Exception as exc:
            logger.warning("llm_enhancement_failed", error=str(exc))

        return response

    async def enhance_recommendation_wording(self, response: AgentResponse) -> AgentResponse:
        if not self.is_available or response.insufficient_evidence:
            return response

        try:
            from google import genai

            client = genai.Client(api_key=self._settings.google_api_key)
            prompt = (
                "Rewrite these remediation recommendations to be clearer. "
                "Keep them non-destructive. Do NOT add new technical claims.\n\n"
                + "\n".join(f"- {a}" for a in response.recommended_actions)
                + "\n\nReturn only a bullet list, one per line."
            )
            result = client.models.generate_content(
                model=self._settings.agent_model,
                contents=prompt,
            )
            text = result.text or ""
            refined = [
                line.lstrip("- ").strip()
                for line in text.strip().split("\n")
                if line.strip()
            ]
            if refined:
                response.recommended_actions = refined
        except Exception as exc:
            logger.warning("llm_recommendation_enhancement_failed", error=str(exc))

        return response
