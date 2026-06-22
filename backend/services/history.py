import json
import uuid
from datetime import UTC, datetime, timedelta

import aiosqlite
import structlog

from backend.models.api import MetricsSnapshot
from backend.models import SeverityLevel
from backend.models.history import (
    HistoryResponse,
    MetricSnapshotRecord,
    TrendChange,
    TrendsResponse,
)

logger = structlog.get_logger(__name__)

METRIC_FIELDS = ("cpu_percent", "memory_percent", "disk_percent_max")


class HistoryService:
    """Persists and analyzes metric snapshots over time using deterministic trend logic."""

    def __init__(self, db_path: str = "./data/incidents.db") -> None:
        self._db_path = db_path

    async def initialize(self) -> None:
        from pathlib import Path

        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS metric_snapshots (
                    id TEXT PRIMARY KEY,
                    recorded_at TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent_max REAL,
                    network_bytes_sent INTEGER,
                    network_bytes_recv INTEGER,
                    database_connected INTEGER,
                    database_latency_ms REAL,
                    service_health_ok INTEGER,
                    anomaly_count INTEGER NOT NULL DEFAULT 0,
                    raw_snapshot TEXT
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_recorded_at "
                "ON metric_snapshots(recorded_at)"
            )
            await db.commit()

    async def record_from_snapshot(
        self,
        snapshot: MetricsSnapshot,
        anomaly_count: int = 0,
    ) -> MetricSnapshotRecord:
        await self.initialize()
        record = self._extract_record(snapshot, anomaly_count)
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO metric_snapshots
                (id, recorded_at, cpu_percent, memory_percent, disk_percent_max,
                 network_bytes_sent, network_bytes_recv, database_connected,
                 database_latency_ms, service_health_ok, anomaly_count, raw_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.recorded_at.isoformat(),
                    record.cpu_percent,
                    record.memory_percent,
                    record.disk_percent_max,
                    record.network_bytes_sent,
                    record.network_bytes_recv,
                    int(record.database_connected) if record.database_connected is not None else None,
                    record.database_latency_ms,
                    int(record.service_health_ok) if record.service_health_ok is not None else None,
                    record.anomaly_count,
                    json.dumps(snapshot.model_dump(mode="json")),
                ),
            )
            await db.commit()
        logger.info("metric_snapshot_recorded", snapshot_id=record.id, anomaly_count=anomaly_count)
        return record

    async def get_history(
        self,
        limit: int = 100,
        since_minutes: int | None = None,
    ) -> HistoryResponse:
        await self.initialize()
        query = "SELECT * FROM metric_snapshots"
        params: list = []
        if since_minutes is not None:
            since = datetime.now(UTC) - timedelta(minutes=since_minutes)
            query += " WHERE recorded_at >= ?"
            params.append(since.isoformat())
        query += " ORDER BY recorded_at DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

        records = [self._row_to_record(row) for row in rows]
        return HistoryResponse(records=records, total=len(records))

    async def compute_trends(self, window_minutes: int = 15) -> TrendsResponse:
        await self.initialize()
        since = datetime.now(UTC) - timedelta(minutes=window_minutes)
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM metric_snapshots WHERE recorded_at >= ? ORDER BY recorded_at ASC",
                (since.isoformat(),),
            )
            rows = await cursor.fetchall()

        records = [self._row_to_record(row) for row in rows]
        if not records:
            return TrendsResponse(
                observations=0,
                window_minutes=window_minutes,
                summaries=["No historical observations in the selected window."],
            )

        moving_averages = self._moving_averages(records)
        trend_changes = self._detect_trend_changes(records, window_minutes)
        current_vs_previous = self._compare_halves(records)
        summaries = self._build_summaries(trend_changes, records, window_minutes)

        return TrendsResponse(
            observations=len(records),
            window_minutes=window_minutes,
            moving_averages=moving_averages,
            trend_changes=trend_changes,
            summaries=summaries,
            current_vs_previous=current_vs_previous,
        )

    def _extract_record(
        self, snapshot: MetricsSnapshot, anomaly_count: int
    ) -> MetricSnapshotRecord:
        cpu = snapshot.system.get("get_cpu_metrics", {})
        memory = snapshot.system.get("get_memory_metrics", {})
        disk = snapshot.system.get("get_disk_metrics", {})
        network = snapshot.system.get("get_network_metrics", {})
        db = snapshot.services.get("check_database", {})

        disk_max = None
        partitions = disk.get("partitions", []) if isinstance(disk, dict) else []
        if partitions:
            disk_max = max(p.get("percent", 0) for p in partitions)

        db_connected = db.get("connected") if isinstance(db, dict) else None
        http_checks = [
            v.get("healthy")
            for v in snapshot.infrastructure.values()
            if isinstance(v, dict) and "healthy" in v
        ]
        service_ok = all(http_checks) if http_checks else None

        return MetricSnapshotRecord(
            id=str(uuid.uuid4()),
            recorded_at=snapshot.collected_at,
            cpu_percent=cpu.get("cpu_percent") if isinstance(cpu, dict) else None,
            memory_percent=memory.get("percent") if isinstance(memory, dict) else None,
            disk_percent_max=disk_max,
            network_bytes_sent=network.get("bytes_sent") if isinstance(network, dict) else None,
            network_bytes_recv=network.get("bytes_recv") if isinstance(network, dict) else None,
            database_connected=db_connected,
            database_latency_ms=db.get("latency_ms") if isinstance(db, dict) else None,
            service_health_ok=service_ok,
            anomaly_count=anomaly_count,
        )

    def _moving_averages(self, records: list[MetricSnapshotRecord]) -> dict[str, float]:
        averages: dict[str, float] = {}
        for field in METRIC_FIELDS:
            values = [getattr(r, field) for r in records if getattr(r, field) is not None]
            if values:
                averages[field] = round(sum(values) / len(values), 2)
        return averages

    def _compare_halves(self, records: list[MetricSnapshotRecord]) -> dict[str, dict[str, float]]:
        mid = len(records) // 2
        if mid == 0:
            return {}
        first_half = records[:mid]
        second_half = records[mid:]
        result: dict[str, dict[str, float]] = {}
        for field in METRIC_FIELDS:
            prev_vals = [getattr(r, field) for r in first_half if getattr(r, field) is not None]
            curr_vals = [getattr(r, field) for r in second_half if getattr(r, field) is not None]
            if prev_vals and curr_vals:
                result[field] = {
                    "previous_avg": round(sum(prev_vals) / len(prev_vals), 2),
                    "current_avg": round(sum(curr_vals) / len(curr_vals), 2),
                }
        return result

    def _detect_trend_changes(
        self, records: list[MetricSnapshotRecord], window_minutes: int
    ) -> list[TrendChange]:
        changes: list[TrendChange] = []
        comparison = self._compare_halves(records)
        labels = {
            "cpu_percent": "CPU",
            "memory_percent": "Memory",
            "disk_percent_max": "Disk",
        }
        for field, label in labels.items():
            if field not in comparison:
                continue
            prev_avg = comparison[field]["previous_avg"]
            curr_avg = comparison[field]["current_avg"]
            delta = curr_avg - prev_avg
            if abs(delta) < 1.0:
                direction = "stable"
            elif delta > 0:
                direction = "increasing"
            else:
                direction = "decreasing"

            sustained = self._is_sustained_increase(records, field) if direction == "increasing" else False
            severity = SeverityLevel.INFO
            if direction == "increasing" and delta >= 20:
                severity = SeverityLevel.CRITICAL
            elif direction == "increasing" and delta >= 10:
                severity = SeverityLevel.WARNING

            if direction != "stable" or sustained:
                changes.append(
                    TrendChange(
                        metric=field,
                        description=(
                            f"{label} {direction} from {prev_avg}% average to "
                            f"{curr_avg}% average over the last {window_minutes} minutes"
                        ),
                        previous_avg=prev_avg,
                        current_avg=curr_avg,
                        window_minutes=window_minutes,
                        direction=direction,
                        sustained=sustained,
                        severity=severity,
                    )
                )
        return changes

    def _is_sustained_increase(
        self, records: list[MetricSnapshotRecord], field: str, min_streak: int = 3
    ) -> bool:
        values = [getattr(r, field) for r in records if getattr(r, field) is not None]
        if len(values) < min_streak:
            return False
        streak = 1
        max_streak = 1
        for i in range(1, len(values)):
            if values[i] > values[i - 1]:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 1
        return max_streak >= min_streak

    def _build_summaries(
        self,
        changes: list[TrendChange],
        records: list[MetricSnapshotRecord],
        window_minutes: int,
    ) -> list[str]:
        summaries = [c.description for c in changes]
        for field, label in {
            "memory_percent": "Memory utilization",
            "cpu_percent": "CPU utilization",
        }.items():
            streak_len = self._consecutive_increase_count(records, field)
            if streak_len >= 3:
                summaries.append(
                    f"{label} increased continuously for {streak_len} observations"
                )
        if not summaries:
            summaries.append(f"Metrics stable over the last {window_minutes} minutes.")
        return summaries

    def _consecutive_increase_count(
        self, records: list[MetricSnapshotRecord], field: str
    ) -> int:
        values = [getattr(r, field) for r in records if getattr(r, field) is not None]
        if len(values) < 2:
            return 0
        streak = 1
        max_streak = 1
        for i in range(len(values) - 1, 0, -1):
            if values[i] > values[i - 1]:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                break
        return max_streak if values[-1] > values[0] else 0

    def _row_to_record(self, row) -> MetricSnapshotRecord:
        return MetricSnapshotRecord(
            id=row["id"],
            recorded_at=datetime.fromisoformat(row["recorded_at"]),
            cpu_percent=row["cpu_percent"],
            memory_percent=row["memory_percent"],
            disk_percent_max=row["disk_percent_max"],
            network_bytes_sent=row["network_bytes_sent"],
            network_bytes_recv=row["network_bytes_recv"],
            database_connected=bool(row["database_connected"]) if row["database_connected"] is not None else None,
            database_latency_ms=row["database_latency_ms"],
            service_health_ok=bool(row["service_health_ok"]) if row["service_health_ok"] is not None else None,
            anomaly_count=row["anomaly_count"] or 0,
        )
