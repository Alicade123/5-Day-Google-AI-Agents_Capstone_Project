import socket
import ssl
import subprocess
import time
from datetime import datetime, timezone

import requests

from backend.config.settings import get_settings
from backend.models.health import (
    DnsResult,
    HttpHealthResult,
    PingResult,
    PortScanResult,
    SslCertificateResult,
)
from backend.models import ToolResult
from backend.tools.base import run_tool


def check_ping(host: str) -> ToolResult[PingResult]:
    def _collect() -> PingResult:
        settings = get_settings()
        if _ping_via_socket(host, settings.ping_timeout_seconds):
            return PingResult(host=host, latency_ms=None, reachable=True)

        latency = _ping_via_subprocess(host, settings.ping_timeout_seconds)
        return PingResult(host=host, latency_ms=latency, reachable=latency is not None)

    return run_tool("check_ping", _collect)


def _ping_via_socket(host: str, timeout: float) -> bool:
    try:
        socket.create_connection((host, 80), timeout=timeout).close()
        return True
    except OSError:
        return False


def _ping_via_subprocess(host: str, timeout: float) -> float | None:
    count_flag = "-n" if _is_windows() else "-c"
    cmd = ["ping", count_flag, "1", "-w", str(int(timeout * 1000)), host]
    if not _is_windows():
        cmd = ["ping", count_flag, "1", "-W", str(int(timeout)), host]
    start = time.perf_counter()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
        if result.returncode == 0:
            return round((time.perf_counter() - start) * 1000, 2)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _is_windows() -> bool:
    import platform

    return platform.system() == "Windows"


def check_http_health(url: str) -> ToolResult[HttpHealthResult]:
    def _collect() -> HttpHealthResult:
        settings = get_settings()
        start = time.perf_counter()
        try:
            response = requests.get(url, timeout=settings.http_timeout_seconds)
            elapsed = round((time.perf_counter() - start) * 1000, 2)
            healthy = 200 <= response.status_code < 400
            return HttpHealthResult(
                url=url,
                status_code=response.status_code,
                response_time_ms=elapsed,
                healthy=healthy,
            )
        except requests.RequestException as exc:
            return HttpHealthResult(url=url, healthy=False, error=str(exc))

    return run_tool("check_http_health", _collect)


def scan_port(host: str, port: int) -> ToolResult[PortScanResult]:
    def _collect() -> PortScanResult:
        settings = get_settings()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(settings.ping_timeout_seconds)
        try:
            result = sock.connect_ex((host, port))
            return PortScanResult(host=host, port=port, open=result == 0)
        finally:
            sock.close()

    return run_tool("scan_port", _collect)


def check_ssl_certificate(hostname: str, port: int = 443) -> ToolResult[SslCertificateResult]:
    def _collect() -> SslCertificateResult:
        context = ssl.create_default_context()
        try:
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
            expires_str = cert.get("notAfter")
            if not expires_str:
                return SslCertificateResult(
                    hostname=hostname, valid=False, error="Certificate expiry not found"
                )
            expires = datetime.strptime(expires_str, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=timezone.utc
            )
            days_remaining = (expires - datetime.now(timezone.utc)).days
            return SslCertificateResult(
                hostname=hostname,
                expires=expires,
                days_remaining=days_remaining,
                valid=days_remaining > 0,
            )
        except Exception as exc:
            return SslCertificateResult(hostname=hostname, valid=False, error=str(exc))

    return run_tool("check_ssl_certificate", _collect)


def resolve_dns(hostname: str) -> ToolResult[DnsResult]:
    def _collect() -> DnsResult:
        try:
            infos = socket.getaddrinfo(hostname, None)
            addresses = sorted({info[4][0] for info in infos})
            return DnsResult(hostname=hostname, addresses=addresses, resolved=bool(addresses))
        except socket.gaierror as exc:
            return DnsResult(hostname=hostname, resolved=False, error=str(exc))

    return run_tool("resolve_dns", _collect)
