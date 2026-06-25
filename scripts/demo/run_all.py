"""Run all Antigravity demo scenarios sequentially."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.demo import (
    scenario_01_cpu_spike,
    scenario_02_memory_leak,
    scenario_03_db_latency,
    scenario_04_incidents_correlation,
)
from scripts.demo._common import write_demo_log


async def run_all() -> None:
    log_path = Path("data/demo/app.log")
    write_demo_log(
        log_path,
        [
            "2026-06-24T10:00:01 INFO Application started",
            "2026-06-24T10:05:12 ERROR Database connection timeout after 5000ms",
            "2026-06-24T10:05:13 ERROR Database connection timeout after 5000ms",
            "2026-06-24T10:06:01 WARNING CPU utilization above 90%",
            "2026-06-24T10:06:45 ERROR OutOfMemoryError: Java heap space",
            "2026-06-24T10:07:02 ERROR Database connection timeout after 5000ms",
            "2026-06-24T10:08:11 CRITICAL Service health check failed",
        ],
    )
    print(f"[demo] Wrote sample log to {log_path}")

    await scenario_01_cpu_spike.run()
    await scenario_02_memory_leak.run()
    await scenario_03_db_latency.run()
    await scenario_04_incidents_correlation.run()

    print("\n[demo] All scenarios seeded. Open dashboard or call /correlation and /history/trends.")


if __name__ == "__main__":
    asyncio.run(run_all())
