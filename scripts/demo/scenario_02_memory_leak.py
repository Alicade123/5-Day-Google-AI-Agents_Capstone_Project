"""Scenario 2: Memory leak — seeds steadily increasing memory utilization."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.demo._common import insert_metric_snapshots


async def run() -> None:
    memory_values = [48.0, 52.0, 57.0, 63.0, 69.0, 74.0, 79.0, 84.0, 88.0, 92.5]
    records = [
        {
            "cpu_percent": 35.0,
            "memory_percent": value,
            "anomaly_count": 1 if value >= 85 else 0,
            "scenario": "memory_leak",
        }
        for value in memory_values
    ]
    count = await insert_metric_snapshots(records)
    print(f"[scenario-02] Seeded {count} memory leak snapshots (peak 92.5%).")
    print("Demo prompts:")
    print('  - "Is there a memory leak on this server?"')
    print('  - GET /history/trends?window_minutes=30')


if __name__ == "__main__":
    asyncio.run(run())
