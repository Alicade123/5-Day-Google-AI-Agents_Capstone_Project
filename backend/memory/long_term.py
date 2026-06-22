import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from backend.memory.interfaces import LongTermMemory
from backend.models import SeverityLevel
from backend.models.incidents import Incident


class SQLiteLongTermMemory(LongTermMemory):
    def __init__(self, db_path: str = "./data/incidents.db") -> None:
        self._db_path = db_path

    async def initialize(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    facts TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
                """
            )
            await db.commit()

    async def save_incident(self, incident: Incident) -> None:
        await self.initialize()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO incidents
                (id, title, summary, severity, facts, recommendations, created_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.id,
                    incident.title,
                    incident.summary,
                    incident.severity.value,
                    json.dumps(incident.facts),
                    json.dumps(incident.recommendations),
                    incident.created_at.isoformat(),
                    incident.resolved_at.isoformat() if incident.resolved_at else None,
                ),
            )
            await db.commit()

    async def list_incidents(self, limit: int = 50) -> list[Incident]:
        await self.initialize()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
        return [self._row_to_incident(row) for row in rows]

    async def get_incident(self, incident_id: str) -> Incident | None:
        await self.initialize()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM incidents WHERE id = ?",
                (incident_id,),
            )
            row = await cursor.fetchone()
        return self._row_to_incident(row) if row else None

    def _row_to_incident(self, row) -> Incident:
        return Incident(
            id=row["id"],
            title=row["title"],
            summary=row["summary"],
            severity=SeverityLevel(row["severity"]),
            facts=json.loads(row["facts"]),
            recommendations=json.loads(row["recommendations"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            resolved_at=(
                datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None
            ),
        )
