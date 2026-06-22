import sqlite3
from pathlib import Path

import pytest

from backend.tools.logs import analyze_logs
from backend.tools.services import check_database, check_service_health


def test_analyze_logs_detects_errors(tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "2026-06-19 10:00:00 INFO Application started\n"
        "2026-06-19 10:01:00 ERROR Connection refused to database\n"
        "2026-06-19 10:01:05 ERROR Connection refused to database\n"
        "2026-06-19 10:02:00 INFO Retrying connection\n",
        encoding="utf-8",
    )

    result = analyze_logs(str(log_file), lines=100)
    assert result.success is True
    assert result.data is not None
    assert len(result.data.errors) == 2
    assert "error-level entries" in result.data.summary.lower()


def test_analyze_logs_missing_file():
    result = analyze_logs("/nonexistent/path/app.log")
    assert result.success is False
    assert result.error is not None


def test_analyze_logs_malformed_content(tmp_path: Path):
    log_file = tmp_path / "malformed.log"
    log_file.write_bytes(b"\xff\xfe binary noise \x00\x01")

    result = analyze_logs(str(log_file))
    assert result.success is True
    assert result.data is not None


def test_check_service_health_finds_python():
    result = check_service_health("python")
    assert result.success is True
    assert result.data is not None
    # On most dev machines a python process is running during tests
    assert isinstance(result.data.running, bool)


def test_check_database_in_memory(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("SELECT 1")
    conn.close()

    monkeypatch.setenv("DATABASE_CHECK_URL", f"sqlite:///{db_path}")
    from backend.config.settings import get_settings

    get_settings.cache_clear()

    result = check_database()
    assert result.success is True
    assert result.data is not None
    assert result.data.connected is True
