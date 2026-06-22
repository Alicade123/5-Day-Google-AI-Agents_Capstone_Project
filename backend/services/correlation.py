import re
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

import structlog

from backend.memory.long_term import SQLiteLongTermMemory
from backend.models import ConfidenceLevel, SeverityLevel
from backend.models.incidents import Incident
from backend.services.history import HistoryService

logger = structlog.get_logger(__name__)


class CorrelationPattern:
    def __init__(
        self,
        pattern: str,
        frequency: int,
        severity: SeverityLevel,
        confidence: ConfidenceLevel,
        description: str,
        related_incidents: list[str] | None = None,
    ) -> None:
        self.pattern = pattern
        self.frequency = frequency
        self.severity = severity
        self.confidence = confidence
        self.description = description
        self.related_incidents = related_incidents or []


class CorrelationResult:
    def __init__(self, patterns: list[CorrelationPattern], window_hours: int) -> None:
        self.patterns = patterns
        self.window_hours = window_hours


class IncidentCorrelationService:
    """Detects repeated incidents, recurring failures, and temporal anomaly patterns."""

    CPU_PATTERN = re.compile(r"cpu|CPU", re.IGNORECASE)
    DB_PATTERN = re.compile(r"database|db|connection", re.IGNORECASE)
    MEMORY_PATTERN = re.compile(r"memory|ram", re.IGNORECASE)

    def __init__(
        self,
        memory: SQLiteLongTermMemory,
        history: HistoryService,
    ) -> None:
        self._memory = memory
        self._history = history

    async def analyze(self, window_hours: int = 1) -> CorrelationResult:
        incidents = await self._memory.list_incidents(limit=200)
        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
        recent = [i for i in incidents if i.created_at >= cutoff]

        patterns: list[CorrelationPattern] = []
        patterns.extend(self._correlate_cpu_spikes(recent, window_hours))
        patterns.extend(self._correlate_database_issues(recent, window_hours))
        patterns.extend(self._correlate_repeated_titles(recent, window_hours))
        patterns.extend(await self._correlate_history_anomalies(window_hours))

        patterns.sort(key=lambda p: p.frequency, reverse=True)
        logger.info("correlation_complete", pattern_count=len(patterns), window_hours=window_hours)
        return CorrelationResult(patterns=patterns, window_hours=window_hours)

    def _correlate_cpu_spikes(
        self, incidents: list[Incident], window_hours: int
    ) -> list[CorrelationPattern]:
        cpu_incidents = [
            i
            for i in incidents
            if any(self.CPU_PATTERN.search(f) for f in i.facts)
            or "cpu" in i.summary.lower()
        ]
        if len(cpu_incidents) < 2:
            return []
        return [
            CorrelationPattern(
                pattern="cpu_spike",
                frequency=len(cpu_incidents),
                severity=SeverityLevel.CRITICAL if len(cpu_incidents) >= 3 else SeverityLevel.WARNING,
                confidence=ConfidenceLevel.HIGH if len(cpu_incidents) >= 3 else ConfidenceLevel.MEDIUM,
                description=f"{len(cpu_incidents)} CPU-related incidents within {window_hours} hour(s)",
                related_incidents=[i.id for i in cpu_incidents],
            )
        ]

    def _correlate_database_issues(
        self, incidents: list[Incident], window_hours: int
    ) -> list[CorrelationPattern]:
        db_incidents = [
            i
            for i in incidents
            if any(self.DB_PATTERN.search(f) for f in i.facts)
            or self.DB_PATTERN.search(i.summary)
        ]
        if len(db_incidents) < 2:
            return []
        return [
            CorrelationPattern(
                pattern="database_latency",
                frequency=len(db_incidents),
                severity=SeverityLevel.WARNING,
                confidence=ConfidenceLevel.MEDIUM,
                description=f"Repeated database issues: {len(db_incidents)} incidents in {window_hours} hour(s)",
                related_incidents=[i.id for i in db_incidents],
            )
        ]

    def _correlate_repeated_titles(
        self, incidents: list[Incident], window_hours: int
    ) -> list[CorrelationPattern]:
        title_groups: dict[str, list[Incident]] = defaultdict(list)
        for incident in incidents:
            normalized = incident.title[:60].lower().strip()
            title_groups[normalized].append(incident)

        patterns: list[CorrelationPattern] = []
        for title, group in title_groups.items():
            if len(group) < 2:
                continue
            patterns.append(
                CorrelationPattern(
                    pattern="repeated_incident",
                    frequency=len(group),
                    severity=SeverityLevel.WARNING,
                    confidence=ConfidenceLevel.MEDIUM,
                    description=f"Repeated incident pattern '{title}' occurred {len(group)} times",
                    related_incidents=[i.id for i in group],
                )
            )
        return patterns

    async def _correlate_history_anomalies(self, window_hours: int) -> list[CorrelationPattern]:
        history = await self._history.get_history(limit=500, since_minutes=window_hours * 60)
        high_anomaly = [r for r in history.records if r.anomaly_count >= 2]
        if len(high_anomaly) < 3:
            return []
        return [
            CorrelationPattern(
                pattern="sustained_anomalies",
                frequency=len(high_anomaly),
                severity=SeverityLevel.CRITICAL,
                confidence=ConfidenceLevel.HIGH,
                description=(
                    f"{len(high_anomaly)} snapshots with multiple anomalies "
                    f"within {window_hours} hour(s)"
                ),
            )
        ]
