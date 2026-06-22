from backend.models import SeverityLevel
from backend.models.logs import AnomalyFinding


class AnomalyDetector:
    """Deterministic threshold-based anomaly detection."""

    def __init__(self, settings):
        self._settings = settings

    def check_cpu(self, percent: float) -> list[AnomalyFinding]:
        return self._check_threshold(
            metric="cpu_percent",
            value=percent,
            warning=self._settings.cpu_warning_percent,
            critical=self._settings.cpu_critical_percent,
            unit="%",
        )

    def check_memory(self, percent: float) -> list[AnomalyFinding]:
        return self._check_threshold(
            metric="memory_percent",
            value=percent,
            warning=self._settings.memory_warning_percent,
            critical=self._settings.memory_critical_percent,
            unit="%",
        )

    def check_disk(self, percent: float) -> list[AnomalyFinding]:
        return self._check_threshold(
            metric="disk_percent",
            value=percent,
            warning=self._settings.disk_warning_percent,
            critical=self._settings.disk_critical_percent,
            unit="%",
        )

    def _check_threshold(
        self,
        metric: str,
        value: float,
        warning: float,
        critical: float,
        unit: str,
    ) -> list[AnomalyFinding]:
        findings: list[AnomalyFinding] = []
        if value >= critical:
            findings.append(
                AnomalyFinding(
                    metric=metric,
                    description=(
                        f"{metric} at {value}{unit} exceeds critical threshold {critical}{unit}"
                    ),
                    severity=SeverityLevel.CRITICAL,
                    observed_value=value,
                    threshold=critical,
                )
            )
        elif value >= warning:
            findings.append(
                AnomalyFinding(
                    metric=metric,
                    description=(
                        f"{metric} at {value}{unit} exceeds warning threshold {warning}{unit}"
                    ),
                    severity=SeverityLevel.WARNING,
                    observed_value=value,
                    threshold=warning,
                )
            )
        return findings
