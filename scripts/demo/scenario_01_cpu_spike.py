"""Scenario 1: CPU spike detected — seeds rising CPU metric snapshots."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.demo._common import insert_metric_snapshots


async def run() -> None:
    cpu_values = [38.0, 42.0, 55.0, 68.0, 79.0, 88.0, 94.0, 97.0, 96.5, 98.2]
    records = [
        {"cpu_percent": value, "memory_percent": 52.0, "anomaly_count": 1 if value >= 90 else 0, "scenario": "cpu_spike"}
        for value in cpu_values
    ]
    count = await insert_metric_snapshots(records)
    print(f"[scenario-01] Seeded {count} CPU spike snapshots (peak 98.2%).")
    print("Demo prompts:")
    print('  - "Why is CPU utilization spiking?"')
    print('  - POST /analyze then GET /history/trends?window_minutes=15')


if __name__ == "__main__":
    asyncio.run(run())
