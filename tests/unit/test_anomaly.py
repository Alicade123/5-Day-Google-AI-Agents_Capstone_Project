import pytest

from backend.config.settings import Settings
from backend.models import SeverityLevel
from backend.services.anomaly import AnomalyDetector


@pytest.fixture
def detector():
    return AnomalyDetector(
        Settings(
            cpu_warning_percent=80,
            cpu_critical_percent=95,
            memory_warning_percent=85,
            memory_critical_percent=95,
            disk_warning_percent=80,
            disk_critical_percent=90,
        )
    )


def test_cpu_critical_anomaly(detector):
    findings = detector.check_cpu(96.0)
    assert len(findings) == 1
    assert findings[0].severity == SeverityLevel.CRITICAL


def test_cpu_warning_anomaly(detector):
    findings = detector.check_cpu(85.0)
    assert len(findings) == 1
    assert findings[0].severity == SeverityLevel.WARNING


def test_cpu_normal_no_anomaly(detector):
    findings = detector.check_cpu(50.0)
    assert len(findings) == 0


def test_memory_critical(detector):
    findings = detector.check_memory(96.0)
    assert findings[0].severity == SeverityLevel.CRITICAL


def test_disk_warning(detector):
    findings = detector.check_disk(82.0)
    assert findings[0].severity == SeverityLevel.WARNING
