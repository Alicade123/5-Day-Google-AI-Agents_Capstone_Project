"""Scenario 4: Repeated incidents correlation — seeds related CPU/DB incidents."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.models import SeverityLevel
from scripts.demo._common import insert_incidents, make_incident


async def run() -> None:
    incidents = [
        make_incident(
            title="CPU spike during batch job",
            summary="CPU utilization exceeded 95% during nightly ETL",
            facts=["CPU utilization reached 96.2%", "Load average spiked to 4.8"],
            severity=SeverityLevel.CRITICAL,
            minutes_ago=55,
        ),
        make_incident(
            title="CPU saturation warning",
            summary="Sustained CPU above threshold for 10 minutes",
            facts=["CPU utilization sustained above 90%", "Top process: data-worker"],
            severity=SeverityLevel.WARNING,
            minutes_ago=42,
        ),
        make_incident(
            title="Database connection latency",
            summary="Database latency increased during CPU spike window",
            facts=["Database latency reached 480ms", "Connection pool near limit"],
            severity=SeverityLevel.WARNING,
            minutes_ago=35,
        ),
        make_incident(
            title="Repeated CPU spike pattern",
            summary="Third CPU spike incident in the last hour",
            facts=["CPU utilization reached 94.1%", "Correlates with prior ETL runs"],
            severity=SeverityLevel.CRITICAL,
            minutes_ago=18,
        ),
        make_incident(
            title="Database timeout under load",
            summary="Database timeouts observed after CPU saturation",
            facts=["Database connection errors increased", "Latency peaked at 620ms"],
            severity=SeverityLevel.CRITICAL,
            minutes_ago=8,
        ),
    ]
    count = await insert_incidents(incidents)
    print(f"[scenario-04] Seeded {count} correlated incidents.")
    print("Demo prompts:")
    print('  - GET /correlation?window_hours=1')
    print('  - "Are there repeated incidents I should investigate?"')


if __name__ == "__main__":
    asyncio.run(run())
