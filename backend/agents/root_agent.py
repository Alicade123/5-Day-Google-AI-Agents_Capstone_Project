from pathlib import Path

from google.adk.agents import Agent

from backend.agents.adk_tools import MONITORING_TOOLS
from backend.config.settings import get_settings

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_instruction.md"


def _load_instruction() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are a server health monitoring agent. "
        "Always use tools to gather evidence. Never fabricate metrics."
    )


def create_root_agent() -> Agent:
    settings = get_settings()
    return Agent(
        name="server_health_monitor",
        model=settings.agent_model,
        instruction=_load_instruction(),
        description=(
            "Monitors server health, analyzes metrics and logs, "
            "and provides grounded remediation recommendations."
        ),
        tools=MONITORING_TOOLS,
    )


root_agent = create_root_agent()
