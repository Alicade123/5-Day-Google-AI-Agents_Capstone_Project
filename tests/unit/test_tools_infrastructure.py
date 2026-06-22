from unittest.mock import MagicMock, patch

import pytest
import requests

from backend.tools.infrastructure import (
    check_http_health,
    check_ping,
    resolve_dns,
    scan_port,
)


def test_check_ping_unreachable_host():
    result = check_ping("192.0.2.1")
    assert result.success is True
    assert result.data is not None
    assert isinstance(result.data.reachable, bool)


def test_scan_port_localhost_closed():
    result = scan_port("127.0.0.1", 59999)
    assert result.success is True
    assert result.data is not None
    assert result.data.open is False


def test_resolve_dns_valid_hostname():
    result = resolve_dns("localhost")
    assert result.success is True
    assert result.data is not None
    assert result.data.resolved is True
    assert len(result.data.addresses) >= 1


def test_resolve_dns_invalid_hostname():
    result = resolve_dns("this-host-definitely-does-not-exist.invalid")
    assert result.success is True
    assert result.data is not None
    assert result.data.resolved is False


@patch("backend.tools.infrastructure.requests.get")
def test_check_http_health_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = check_http_health("http://example.com/health")
    assert result.success is True
    assert result.data is not None
    assert result.data.healthy is True
    assert result.data.status_code == 200


@patch("backend.tools.infrastructure.requests.get")
def test_check_http_health_network_failure(mock_get):
    mock_get.side_effect = requests.ConnectionError("connection refused")

    result = check_http_health("http://example.com/health")
    assert result.success is True
    assert result.data is not None
    assert result.data.healthy is False
    assert result.data.error is not None
