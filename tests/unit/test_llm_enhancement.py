import pytest

from backend.models import ConfidenceLevel
from backend.models.logs import AgentResponse
from backend.services.llm_enhancement import LLMEnhancementService


@pytest.mark.asyncio
async def test_llm_enhancement_skipped_without_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    from backend.config.settings import get_settings

    get_settings.cache_clear()

    service = LLMEnhancementService()
    assert service.is_available is False

    response = AgentResponse(
        facts=["CPU is 50%"],
        possible_explanations=["CPU is normal"],
        confidence=ConfidenceLevel.MEDIUM,
        recommended_actions=["Monitor"],
    )
    enhanced = await service.enhance_explanations(response)
    assert enhanced.possible_explanations == ["CPU is normal"]
