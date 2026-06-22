# Tool Definitions — Structured Schemas

Every tool returns a `ToolResult` envelope:

```json
{
  "success": true,
  "data": { },
  "error": null,
  "executed_at": "2026-06-19T12:00:00Z",
  "duration_ms": 12.5
}
```

## System Tools

### get_cpu_metrics

```json
{
  "cpu_percent": 42.5,
  "per_cpu_percent": [40.0, 45.0],
  "load_average": [1.2, 1.5, 1.8]
}
```

### get_memory_metrics

```json
{
  "used_bytes": 8589934592,
  "available_bytes": 4294967296,
  "total_bytes": 12884901888,
  "percent": 66.7
}
```

### get_disk_metrics

```json
{
  "partitions": [
    {
      "device": "C:\\",
      "mountpoint": "C:\\",
      "total_bytes": 500000000000,
      "used_bytes": 350000000000,
      "free_bytes": 150000000000,
      "percent": 70.0
    }
  ]
}
```

### get_network_metrics

```json
{
  "bytes_sent": 1024000,
  "bytes_recv": 2048000,
  "packets_sent": 5000,
  "packets_recv": 8000,
  "active_connections": 42
}
```

### get_process_metrics

```json
{
  "processes": [
    {"pid": 1234, "name": "python", "cpu_percent": 15.2, "memory_percent": 5.1}
  ]
}
```

### get_uptime_metrics

```json
{
  "uptime_seconds": 86400,
  "boot_time": "2026-06-18T12:00:00Z",
  "load_average": [0.5, 0.6, 0.7]
}
```

## Infrastructure Tools

### check_ping

```json
{"host": "8.8.8.8", "latency_ms": 12.3, "reachable": true}
```

### check_http_health

```json
{"url": "http://localhost:8000/health", "status_code": 200, "response_time_ms": 45.2, "healthy": true}
```

### scan_port

```json
{"host": "localhost", "port": 443, "open": true}
```

### check_ssl_certificate

```json
{"hostname": "example.com", "expires": "2026-12-01T00:00:00Z", "days_remaining": 165, "valid": true}
```

### resolve_dns

```json
{"hostname": "example.com", "addresses": ["93.184.216.34"], "resolved": true}
```

## Service Tools

### check_service_health

```json
{"name": "api", "running": true, "status": "running", "pid": 5678}
```

### check_database

```json
{"connected": true, "latency_ms": 3.2, "database_type": "sqlite"}
```

## Log Analyzer

### analyze_logs

```json
{
  "path": "/var/log/app.log",
  "lines_analyzed": 500,
  "errors": [
    {"line": 42, "timestamp": "...", "message": "Connection refused", "level": "ERROR"}
  ],
  "patterns": [
    {"pattern": "Connection refused", "count": 15, "severity": "CRITICAL"}
  ],
  "summary": "15 connection errors in last 500 lines"
}
```
