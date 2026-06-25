"""Final pre-submission verification — PASS/FAIL report for Kaggle readiness."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_DIR = PROJECT_ROOT / "docs" / "screenshots"
REQUIRED_SCREENSHOTS = [
    "01_dashboard.png",
    "02_metrics.png",
    "03_anomalies.png",
    "04_cpu_spike.png",
    "05_memory_leak.png",
    "06_incident_correlation.png",
    "07_agent_explanation.png",
    "08_mcp_architecture.png",
]
ARCHITECTURE_DIAGRAM = PROJECT_ROOT / "docs" / "architecture_diagram.png"
DEFAULT_BACKEND = os.getenv("CHECK_BACKEND_URL", "http://127.0.0.1:8000")
DEFAULT_FRONTEND = os.getenv("CHECK_FRONTEND_URL", "http://127.0.0.1:5173")


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    results: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.results.append(CheckResult(name=name, passed=passed, detail=detail))

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def print_report(self) -> int:
        print("\n" + "=" * 60)
        print("FINAL DEMO CHECK — KAGGLE SUBMISSION READINESS")
        print("=" * 60)
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            line = f"[{status}] {result.name}"
            if result.detail:
                line += f" — {result.detail}"
            print(line)
        print("-" * 60)
        print(f"TOTAL: {self.passed_count} passed, {self.failed_count} failed")
        overall = "PASS" if self.failed_count == 0 else "FAIL"
        print(f"OVERALL: {overall}")
        print("=" * 60 + "\n")
        return 0 if self.failed_count == 0 else 1


def _port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _load_api_key() -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("API_KEY="):
            value = line.split("=", 1)[1].strip()
            return value or None
    return None


def _api_headers() -> dict[str, str]:
    key = _load_api_key()
    return {"X-API-Key": key} if key else {}


def check_backend_running(report: Report, backend: str) -> None:
    host = backend.split("://")[1].split(":")[0]
    port = int(backend.rsplit(":", 1)[-1])
    report.add("Backend port listening", _port_open(host, port), f"{host}:{port}")


def check_frontend_running(report: Report, frontend: str) -> None:
    host = frontend.split("://")[1].split(":")[0]
    port = int(frontend.rsplit(":", 1)[-1])
    report.add("Frontend port listening", _port_open(host, port), f"{host}:{port}")


def check_api_endpoints(report: Report, backend: str) -> None:
    headers = _api_headers()
    endpoints = [
        ("GET /health", "/health", [200]),
        ("GET /metrics", "/metrics", [200]),
        ("GET /history/trends", "/history/trends?window_minutes=15", [200]),
        ("GET /incidents", "/incidents", [200]),
        ("GET /correlation", "/correlation?window_hours=1", [200]),
        ("POST /analyze", "/analyze", [200]),
    ]
    try:
        with httpx.Client(timeout=90.0, headers=headers) as client:
            for label, path, ok_codes in endpoints:
                method, route = label.split(" ", 1)
                if method == "POST":
                    response = client.post(f"{backend.rstrip('/')}{route}")
                else:
                    response = client.get(f"{backend.rstrip('/')}{route}")
                report.add(
                    f"API {label}",
                    response.status_code in ok_codes,
                    f"status={response.status_code}",
                )
    except httpx.HTTPError as exc:
        report.add("API connectivity", False, str(exc))


def check_frontend_page(report: Report, frontend: str) -> None:
    try:
        response = httpx.get(frontend, timeout=10.0)
        report.add(
            "Frontend HTTP response",
            response.status_code == 200,
            f"status={response.status_code}",
        )
    except httpx.HTTPError as exc:
        report.add("Frontend HTTP response", False, str(exc))


async def check_demo_scenarios(report: Report) -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    scenarios = [
        "scenario_01_cpu_spike",
        "scenario_02_memory_leak",
        "scenario_03_db_latency",
        "scenario_04_incidents_correlation",
    ]
    for name in scenarios:
        try:
            module = importlib.import_module(f"scripts.demo.{name}")
            await module.run()
            report.add(f"Demo {name}", True)
        except Exception as exc:
            report.add(f"Demo {name}", False, str(exc))


def check_screenshots(report: Report) -> None:
    for filename in REQUIRED_SCREENSHOTS:
        path = SCREENSHOT_DIR / filename
        report.add(f"Screenshot {filename}", path.exists(), str(path) if path.exists() else "missing")
    report.add(
        "Architecture diagram PNG",
        ARCHITECTURE_DIAGRAM.exists(),
        str(ARCHITECTURE_DIAGRAM) if ARCHITECTURE_DIAGRAM.exists() else "missing",
    )


def check_mcp_server(report: Report) -> None:
    try:
        from backend.mcp.mcp_server import mcp
        from backend.mcp.tool_adapters import MCP_TOOL_NAMES, execute_mcp_tool

        tool_count = len(MCP_TOOL_NAMES)
        cpu = execute_mcp_tool("get_cpu_metrics")
        report.add("MCP module loads", True, f"{tool_count} tools defined")
        report.add(
            "MCP get_cpu_metrics",
            cpu.get("success") is True,
            "deterministic tool execution",
        )
        _ = mcp  # server object constructed
        report.add("MCP server object", True, "backend.mcp.mcp_server")
    except Exception as exc:
        report.add("MCP server", False, str(exc))


def check_evaluation(report: Report, run_eval: bool) -> None:
    if not run_eval:
        eval_path = PROJECT_ROOT / "backend" / "evaluations" / "runner.py"
        report.add("Evaluation runner present", eval_path.exists(), str(eval_path))
        return
    try:
        result = subprocess.run(
            [sys.executable, "-m", "backend.evaluations.runner"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        report.add(
            "Evaluation runner",
            result.returncode == 0,
            (result.stdout or result.stderr)[-200:],
        )
    except subprocess.TimeoutExpired:
        report.add("Evaluation runner", False, "timed out after 180s")
    except Exception as exc:
        report.add("Evaluation runner", False, str(exc))


def check_env_configuration(report: Report) -> None:
    env_path = PROJECT_ROOT / ".env"
    report.add(".env file exists", env_path.exists())
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        has_google = any(
            line.startswith("GOOGLE_API_KEY=") and line.strip() != "GOOGLE_API_KEY="
            for line in content.splitlines()
        )
        api_key_set = any(
            line.startswith("API_KEY=") and line.split("=", 1)[1].strip()
            for line in content.splitlines()
        )
        report.add("GOOGLE_API_KEY configured", has_google, "required for live agent queries")
        if api_key_set:
            report.add(
                "API_KEY empty for local dashboard",
                False,
                "Clear API_KEY or set VITE_API_KEY in frontend/.env",
            )
        else:
            report.add("API_KEY empty for local dashboard", True)


async def run_checks(backend: str, frontend: str, run_eval: bool) -> Report:
    report = Report()
    check_backend_running(report, backend)
    check_frontend_running(report, frontend)
    check_frontend_page(report, frontend)
    check_api_endpoints(report, backend)
    await check_demo_scenarios(report)
    check_screenshots(report)
    check_mcp_server(report)
    check_evaluation(report, run_eval=run_eval)
    check_env_configuration(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Final Kaggle submission verification.")
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--frontend", default=DEFAULT_FRONTEND)
    parser.add_argument("--run-eval", action="store_true", help="Execute full eval runner (slower).")
    args = parser.parse_args()

    report = asyncio.run(run_checks(args.backend, args.frontend, run_eval=args.run_eval))
    return report.print_report()


if __name__ == "__main__":
    raise SystemExit(main())
