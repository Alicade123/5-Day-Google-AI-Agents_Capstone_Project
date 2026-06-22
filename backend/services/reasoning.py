from backend.config.settings import Settings, get_settings
from backend.models import ConfidenceLevel, SeverityLevel
from backend.models.api import AnalysisResult, MetricsSnapshot
from backend.models.logs import AgentResponse
from backend.services.anomaly import AnomalyDetector


class ReasoningService:
    """Correlates tool outputs into facts, anomalies, and grounded explanations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._detector = AnomalyDetector(self._settings)

    def analyze_snapshot(self, snapshot: MetricsSnapshot) -> AnalysisResult:
        facts = self._extract_facts(snapshot)
        anomalies = self._detect_anomalies(snapshot)
        explanations = self._build_explanations(anomalies, snapshot)
        actions = self._recommend_actions(anomalies, snapshot)
        severity = self._overall_severity(anomalies)

        agent_response = AgentResponse(
            facts=facts,
            possible_explanations=explanations,
            confidence=self._confidence(facts, anomalies, snapshot),
            recommended_actions=actions,
            anomalies=anomalies,
            insufficient_evidence=snapshot.success_count == 0,
            raw_tool_summary={
                "tool_count": snapshot.tool_count,
                "success_count": snapshot.success_count,
                "failures": snapshot.failures,
            },
        )

        if snapshot.success_count == 0:
            agent_response.possible_explanations = [
                "I could not obtain sufficient evidence."
            ]
            agent_response.recommended_actions = [
                "Verify monitoring agent permissions and configured targets."
            ]

        return AnalysisResult(
            snapshot=snapshot,
            anomalies=anomalies,
            facts=facts,
            possible_explanations=explanations,
            recommended_actions=actions,
            overall_severity=severity,
            agent_response=agent_response,
        )

    def _extract_facts(self, snapshot: MetricsSnapshot) -> list[str]:
        facts: list[str] = []
        cpu = snapshot.system.get("get_cpu_metrics", {})
        if "cpu_percent" in cpu:
            facts.append(f"CPU utilization is {cpu['cpu_percent']}%")
        memory = snapshot.system.get("get_memory_metrics", {})
        if "percent" in memory:
            facts.append(f"Memory usage is {memory['percent']}%")
        disk = snapshot.system.get("get_disk_metrics", {})
        partitions = disk.get("partitions", [])
        for part in partitions[:3]:
            facts.append(
                f"Disk {part.get('mountpoint', 'unknown')} usage is {part.get('percent', 0)}%"
            )
        uptime = snapshot.system.get("get_uptime_metrics", {})
        if "uptime_seconds" in uptime:
            hours = round(uptime["uptime_seconds"] / 3600, 1)
            facts.append(f"System uptime is {hours} hours")
        for key, value in snapshot.infrastructure.items():
            if isinstance(value, dict) and "healthy" in value:
                status = "healthy" if value["healthy"] else "unhealthy"
                facts.append(f"HTTP check {value.get('url', key)} is {status}")
            elif isinstance(value, dict) and "reachable" in value:
                status = "reachable" if value["reachable"] else "unreachable"
                facts.append(f"Host {value.get('host', key)} is {status}")
        db = snapshot.services.get("check_database", {})
        if "connected" in db:
            status = "connected" if db["connected"] else "disconnected"
            facts.append(f"Database is {status}")
        for key, value in snapshot.logs.items():
            if isinstance(value, dict) and value.get("summary"):
                facts.append(value["summary"])
        return facts

    def _detect_anomalies(self, snapshot: MetricsSnapshot):
        findings = []
        cpu = snapshot.system.get("get_cpu_metrics", {})
        if "cpu_percent" in cpu:
            findings.extend(self._detector.check_cpu(float(cpu["cpu_percent"])))
        memory = snapshot.system.get("get_memory_metrics", {})
        if "percent" in memory:
            findings.extend(self._detector.check_memory(float(memory["percent"])))
        disk = snapshot.system.get("get_disk_metrics", {})
        for part in disk.get("partitions", []):
            if "percent" in part:
                findings.extend(self._detector.check_disk(float(part["percent"])))
        return findings

    def _build_explanations(self, anomalies, snapshot: MetricsSnapshot) -> list[str]:
        if not anomalies:
            if snapshot.failures:
                return ["Some monitoring tools failed; partial evidence may limit diagnosis."]
            return ["No threshold anomalies detected in collected metrics."]
        explanations = []
        for finding in anomalies:
            explanations.append(finding.description)
        log_errors = sum(
            len(v.get("errors", []))
            for v in snapshot.logs.values()
            if isinstance(v, dict)
        )
        if log_errors > 0:
            explanations.append(
                f"Application logs show {log_errors} error-level entries that may contribute."
            )
        unhealthy = [
            v.get("url", k)
            for k, v in snapshot.infrastructure.items()
            if isinstance(v, dict) and v.get("healthy") is False
        ]
        if unhealthy:
            explanations.append(
                f"HTTP health checks failed for: {', '.join(str(u) for u in unhealthy)}"
            )
        return explanations

    def _recommend_actions(self, anomalies, snapshot: MetricsSnapshot) -> list[str]:
        actions: list[str] = []
        metrics = {a.metric for a in anomalies}
        if "cpu_percent" in metrics:
            actions.append("Investigate top CPU-consuming processes and consider scaling compute.")
        if "memory_percent" in metrics:
            actions.append("Review memory-heavy processes; consider increasing available RAM.")
        if "disk_percent" in metrics:
            actions.append("Free disk space or expand storage on affected partitions.")
        for value in snapshot.logs.values():
            if isinstance(value, dict) and value.get("patterns"):
                actions.append("Investigate recurring log error patterns for root cause.")
        if not actions and snapshot.failures:
            actions.append("Fix tool failures to restore full monitoring visibility.")
        if not actions:
            actions.append("Continue routine monitoring; no immediate remediation required.")
        return actions

    def _overall_severity(self, anomalies) -> SeverityLevel:
        if any(a.severity == SeverityLevel.CRITICAL for a in anomalies):
            return SeverityLevel.CRITICAL
        if any(a.severity == SeverityLevel.WARNING for a in anomalies):
            return SeverityLevel.WARNING
        return SeverityLevel.INFO

    def _confidence(self, facts, anomalies, snapshot: MetricsSnapshot) -> ConfidenceLevel:
        if snapshot.success_count == 0:
            return ConfidenceLevel.LOW
        if len(facts) >= 4 and anomalies:
            return ConfidenceLevel.HIGH
        if len(facts) >= 2:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW
