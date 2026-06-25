"""Scenario 3: Database latency increase — seeds rising DB latency snapshots."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.demo._common import insert_metric_snapshots


async def run() -> None:
    latency_values = [8.0, 12.0, 25.0, 48.0, 95.0, 180.0, 310.0, 420.0, 510.0, 620.0]
    records = [
        {
            "cpu_percent": 40.0,
            "memory_percent": 55.0,
            "database_latency_ms": latency,
            "anomaly_count": 1 if latency >= 200 else 0,
            "scenario": "db_latency",
        }
        for latency in latency_values
    ]
    count = await insert_metric_snapshots(records)
    print(f"[scenario-03] Seeded {count} database latency snapshots (peak 620ms).")
    print("Demo prompts:")
    print('  - "Check database connectivity and latency trends"')
    print('  - MCP tool: check_database + get_history')


if __name__ == "__main__":
    asyncio.run(run())
