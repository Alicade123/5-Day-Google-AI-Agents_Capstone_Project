from datetime import UTC, datetime

from backend.agents.executor import ToolExecutor
from backend.agents.planner import Planner
from backend.agents.response import ResponseGenerator
from backend.config.settings import Settings, get_settings
from backend.models.api import AnalysisResult, MetricsSnapshot
from backend.models.logs import AgentResponse
from backend.services.llm_enhancement import LLMEnhancementService
from backend.services.metrics_collector import MetricsCollector
from backend.services.reasoning import ReasoningService
from backend.services.tool_registry import get_tool_registry


class AgentOrchestrator:
    """End-to-end agent workflow: plan → execute → correlate → respond."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._planner = Planner(
            log_paths=self._settings.csv_list(self._settings.log_paths),
            http_urls=self._settings.csv_list(self._settings.http_health_urls),
            ping_hosts=self._settings.csv_list(self._settings.ping_hosts),
            ports=self._parse_ports(),
            services=self._settings.csv_list(self._settings.monitored_services),
        )
        self._executor = ToolExecutor(registry=get_tool_registry())
        self._collector = MetricsCollector(settings=self._settings)
        self._reasoning = ReasoningService(settings=self._settings)
        self._response = ResponseGenerator()
        self._llm = LLMEnhancementService()

    def _parse_ports(self) -> list[int]:
        ports: list[int] = []
        for port_str in self._settings.csv_list(self._settings.monitored_ports):
            try:
                ports.append(int(port_str))
            except ValueError:
                continue
        return ports

    async def query(self, user_query: str) -> AgentResponse:
        plan = self._planner.plan(user_query)
        tool_results = await self._executor.execute_plan_parallel(plan)
        snapshot = self._tool_results_to_snapshot(tool_results)
        analysis = self._reasoning.analyze_snapshot(snapshot)
        response = self._response.generate(analysis)
        if self._llm.is_available:
            response = await self._llm.enhance_explanations(response)
            response = await self._llm.enhance_recommendation_wording(response)
        return response

    async def analyze_full(self) -> AnalysisResult:
        snapshot = await self._collector.collect_full_snapshot()
        return self._reasoning.analyze_snapshot(snapshot)

    def _tool_results_to_snapshot(self, results: dict) -> MetricsSnapshot:
        system: dict = {}
        infrastructure: dict = {}
        services: dict = {}
        logs: dict = {}

        for key, result in results.items():
            normalized = self._collector._normalize_result(result)
            category = self._categorize_tool_key(key)
            if category == "system":
                system[key] = normalized
            elif category == "infrastructure":
                infrastructure[key] = normalized
            elif category == "services":
                services[key] = normalized
            elif category == "logs":
                logs[key] = normalized

        failures = [f"{k}: {r.error}" for k, r in results.items() if not r.success]
        success_count = sum(1 for r in results.values() if r.success)

        return MetricsSnapshot(
            collected_at=datetime.now(UTC),
            system=system,
            infrastructure=infrastructure,
            services=services,
            logs=logs,
            failures=failures,
            tool_count=len(results),
            success_count=success_count,
        )

    @staticmethod
    def _categorize_tool_key(key: str) -> str:
        if key.startswith("get_"):
            return "system"
        if key.startswith(("check_ping", "check_http_health", "scan_port",
                           "check_ssl_certificate", "resolve_dns")):
            return "infrastructure"
        if key.startswith(("check_service_health", "check_database")):
            return "services"
        if key.startswith("analyze_logs"):
            return "logs"
        return "system"
