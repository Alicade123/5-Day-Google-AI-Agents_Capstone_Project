"""Shared helpers for Antigravity demo scenario scripts."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

from backend.config.settings import get_settings
from backend.memory.long_term import SQLiteLongTermMemory
from backend.models import SeverityLevel
from backend.models.incidents import Incident
from backend.services.history import HistoryService


def db_path() -> str:
    return get_settings().database_url.replace("sqlite+aiosqlite:///", "")


async def ensure_schema() -> None:
    history = HistoryService(db_path=db_path())
    await history.initialize()
    memory = SQLiteLongTermMemory(db_path=db_path())
    await memory.initialize()


async def insert_metric_snapshots(
    records: list[dict],
    *,
    base_time: datetime | None = None,
) -> int:
    """Insert metric snapshot rows for demo trend visualization."""
    await ensure_schema()
    path = db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    anchor = base_time or datetime.now(UTC)

    async with aiosqlite.connect(path) as db:
        for index, record in enumerate(records):
            recorded_at = anchor - timedelta(minutes=len(records) - index - 1)
            snapshot_id = str(uuid.uuid4())
            await db.execute(
                """
                INSERT INTO metric_snapshots
                (id, recorded_at, cpu_percent, memory_percent, disk_percent_max,
                 network_bytes_sent, network_bytes_recv, database_connected,
                 database_latency_ms, service_health_ok, anomaly_count, raw_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    recorded_at.isoformat(),
                    record.get("cpu_percent"),
                    record.get("memory_percent"),
                    record.get("disk_percent_max", 55.0),
                    record.get("network_bytes_sent", 1_000_000),
                    record.get("network_bytes_recv", 2_000_000),
                    int(record.get("database_connected", True)),
                    record.get("database_latency_ms", 12.0),
                    int(record.get("service_health_ok", True)),
                    record.get("anomaly_count", 0),
                    json.dumps({"demo": True, "scenario": record.get("scenario", "demo")}),
                ),
            )
        await db.commit()
    return len(records)


async def insert_incidents(incidents: list[Incident]) -> int:
    await ensure_schema()
    memory = SQLiteLongTermMemory(db_path=db_path())
    for incident in incidents:
        await memory.save_incident(incident)
    return len(incidents)


def make_incident(
    *,
    title: str,
    summary: str,
    facts: list[str],
    severity: SeverityLevel = SeverityLevel.WARNING,
    minutes_ago: int = 0,
    recommendations: list[str] | None = None,
) -> Incident:
    return Incident(
        id=str(uuid.uuid4()),
        title=title,
        summary=summary,
        severity=severity,
        facts=facts,
        recommendations=recommendations or ["Investigate root cause and scale resources if needed."],
        created_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    )


def write_demo_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
