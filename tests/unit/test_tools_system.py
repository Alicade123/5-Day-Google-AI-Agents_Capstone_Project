from backend.tools.system import (
    get_cpu_metrics,
    get_disk_metrics,
    get_memory_metrics,
    get_network_metrics,
    get_process_metrics,
    get_uptime_metrics,
)


def test_get_cpu_metrics_returns_valid_data():
    result = get_cpu_metrics()
    assert result.success is True
    assert result.data is not None
    assert 0 <= result.data.cpu_percent <= 100
    assert result.duration_ms >= 0


def test_get_memory_metrics_returns_valid_data():
    result = get_memory_metrics()
    assert result.success is True
    assert result.data is not None
    assert result.data.total_bytes > 0
    assert 0 <= result.data.percent <= 100


def test_get_disk_metrics_returns_partitions():
    result = get_disk_metrics()
    assert result.success is True
    assert result.data is not None
    assert len(result.data.partitions) >= 1
    partition = result.data.partitions[0]
    assert partition.percent >= 0


def test_get_network_metrics_returns_counters():
    result = get_network_metrics()
    assert result.success is True
    assert result.data is not None
    assert result.data.bytes_sent >= 0
    assert result.data.bytes_recv >= 0


def test_get_process_metrics_respects_limit():
    result = get_process_metrics(limit=5)
    assert result.success is True
    assert result.data is not None
    assert len(result.data.processes) <= 5
    if result.data.processes:
        proc = result.data.processes[0]
        assert proc.pid >= 0
        assert proc.name


def test_get_uptime_metrics_positive():
    result = get_uptime_metrics()
    assert result.success is True
    assert result.data is not None
    assert result.data.uptime_seconds > 0
