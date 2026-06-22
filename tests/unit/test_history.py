import pytest

from backend.models.api import MetricsSnapshot
from backend.services.history import HistoryService


@pytest.mark.asyncio
async def test_record_and_retrieve_history(tmp_path):
    db_path = str(tmp_path / "history.db")
    service = HistoryService(db_path=db_path)
    snapshot = MetricsSnapshot(
        system={
            "get_cpu_metrics": {"cpu_percent": 45.0},
            "get_memory_metrics": {"percent": 70.0},
            "get_disk_metrics": {"partitions": [{"percent": 55.0}]},
            "get_network_metrics": {"bytes_sent": 1000, "bytes_recv": 2000},
        },
        services={"check_database": {"connected": True, "latency_ms": 2.5}},
        tool_count=5,
        success_count=5,
    )
    record = await service.record_from_snapshot(snapshot, anomaly_count=1)
    assert record.cpu_percent == 45.0
    assert record.anomaly_count == 1

    history = await service.get_history(limit=10)
    assert history.total == 1
    assert history.records[0].memory_percent == 70.0


@pytest.mark.asyncio
async def test_trend_detection_increasing_cpu(tmp_path):
    db_path = str(tmp_path / "trends.db")
    service = HistoryService(db_path=db_path)

    for cpu in [30.0, 40.0, 50.0, 60.0, 70.0, 75.0, 79.0]:
        snapshot = MetricsSnapshot(
            system={
                "get_cpu_metrics": {"cpu_percent": cpu},
                "get_memory_metrics": {"percent": 50.0},
                "get_disk_metrics": {"partitions": []},
            },
            tool_count=2,
            success_count=2,
        )
        await service.record_from_snapshot(snapshot)

    trends = await service.compute_trends(window_minutes=60)
    assert trends.observations == 7
    assert "cpu_percent" in trends.moving_averages
    assert any("CPU" in s for s in trends.summaries)


@pytest.mark.asyncio
async def test_sustained_memory_increase(tmp_path):
    db_path = str(tmp_path / "memory_trend.db")
    service = HistoryService(db_path=db_path)

    for mem in [50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]:
        snapshot = MetricsSnapshot(
            system={
                "get_cpu_metrics": {"cpu_percent": 30.0},
                "get_memory_metrics": {"percent": mem},
                "get_disk_metrics": {"partitions": []},
            },
            tool_count=2,
            success_count=2,
        )
        await service.record_from_snapshot(snapshot)

    trends = await service.compute_trends(window_minutes=60)
    assert any("Memory" in s and "continuously" in s for s in trends.summaries)
