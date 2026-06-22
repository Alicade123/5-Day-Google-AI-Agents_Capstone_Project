import json
import time
from pathlib import Path

import yaml

from backend.agents.executor import ToolExecutor
from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.planner import Planner
from backend.config.settings import get_settings
from backend.evaluations.metrics import EvalMetrics
from backend.evaluations.schema import EvalCase, EvalDataset, EvalCriterion
from backend.models.logs import AgentResponse

DATASET_PATH = Path(__file__).parent / "datasets" / "default.json"
CONFIG_PATH = Path(__file__).parent / "eval_config.yaml"


class EvalCaseResult:
    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        self.checks: dict[str, dict] = {}
        self.tools_used: list[str] = []
        self.latency_ms: float = 0.0
        self.passed: bool = False
        self.score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "score": round(self.score, 3),
            "latency_ms": round(self.latency_ms, 2),
            "tools_used": self.tools_used,
            "checks": self.checks,
        }


class EvalRunner:
    """Runs evaluation dataset against the agent orchestrator with deterministic grading."""

    def __init__(self, orchestrator: AgentOrchestrator | None = None) -> None:
        self._orchestrator = orchestrator or AgentOrchestrator()
        self._planner = self._orchestrator._planner
        self._executor = ToolExecutor()

    def load_dataset(self, path: Path | None = None) -> EvalDataset:
        data = json.loads((path or DATASET_PATH).read_text(encoding="utf-8"))
        cases = [EvalCase(**item) for item in data]
        config = self.load_config()
        criteria = [EvalCriterion(**c) for c in config.get("criteria", [])]
        return EvalDataset(name="default", cases=cases, criteria=criteria)

    def load_config(self) -> dict:
        if CONFIG_PATH.exists():
            return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        return {"thresholds": {"pass_score": 0.75, "max_latency_ms": 30000}}

    async def run_case(self, case: EvalCase) -> EvalCaseResult:
        result = EvalCaseResult(case.id)
        start = time.perf_counter()

        plan = self._planner.plan(case.query)
        result.tools_used = [inv.tool_name for inv in plan.tools]
        tool_results = await self._executor.execute_plan_parallel(plan)
        response = await self._orchestrator.query(case.query)

        result.latency_ms = (time.perf_counter() - start) * 1000
        tool_evidence = {
            k: v.data.model_dump(mode="json") if v.success and v.data else v.error
            for k, v in tool_results.items()
        }

        passed_checks = 0
        total_checks = len(case.required_checks)
        for check_name in case.required_checks:
            checker = EvalMetrics.CHECK_MAP.get(check_name)
            if checker is None:
                result.checks[check_name] = {"passed": False, "detail": "unknown check"}
                continue
            ok, detail = checker(response, case, result.tools_used, tool_evidence)
            result.checks[check_name] = {"passed": ok, "detail": detail}
            if ok:
                passed_checks += 1

        config = self.load_config()
        max_latency = config.get("thresholds", {}).get("max_latency_ms", 30000)
        latency_ok = result.latency_ms <= max_latency
        result.checks["latency"] = {
            "passed": latency_ok,
            "detail": f"latency={result.latency_ms:.0f}ms, max={max_latency}ms",
        }
        if latency_ok:
            passed_checks += 1
            total_checks += 1
        else:
            total_checks += 1

        result.score = passed_checks / total_checks if total_checks else 0.0
        pass_threshold = config.get("thresholds", {}).get("pass_score", 0.75)
        result.passed = result.score >= pass_threshold
        return result

    async def run_all(self, dataset: EvalDataset | None = None) -> dict:
        dataset = dataset or self.load_dataset()
        results = []
        for case in dataset.cases:
            case_result = await self.run_case(case)
            results.append(case_result.to_dict())

        passed = sum(1 for r in results if r["passed"])
        return {
            "dataset": dataset.name,
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": round(passed / len(results), 3) if results else 0.0,
            "results": results,
        }


async def _main() -> None:
    runner = EvalRunner()
    report = await runner.run_all()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
