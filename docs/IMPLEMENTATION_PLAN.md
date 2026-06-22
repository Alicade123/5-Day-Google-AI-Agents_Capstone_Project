# Implementation Plan

## File Structure

```
Capstone_Project/
├── .agents-cli-spec.md
├── .env.example
├── pyproject.toml
├── README.md
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # Pydantic Settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── metrics.py             # CPU, Memory, Disk, etc.
│   │   ├── health.py              # HTTP, ping, port, ssl, dns
│   │   ├── logs.py                # Log analysis models
│   │   ├── agent.py               # AgentResponse, AnalysisResult
│   │   └── incidents.py           # Incident records
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py                # ToolResult wrapper
│   │   ├── system.py              # cpu, memory, disk, network, process, uptime
│   │   ├── infrastructure.py      # ping, http, port, ssl, dns
│   │   ├── services.py            # service health, database
│   │   └── logs.py                # log analyzer
│   ├── services/
│   │   ├── __init__.py
│   │   ├── anomaly.py             # Spike/trend detection
│   │   ├── reasoning.py           # Correlation engine
│   │   ├── incidents.py           # Incident CRUD
│   │   └── metrics_collector.py   # Aggregate all metrics
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── short_term.py          # Session store
│   │   └── long_term.py           # SQLite persistence
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── root_agent.py          # ADK Agent definition
│   │   ├── planner.py
│   │   ├── executor.py
│   │   └── response.py
│   ├── prompts/
│   │   └── system_instruction.md
│   └── api/
│       ├── __init__.py
│       ├── routes/
│       │   ├── health.py
│       │   ├── metrics.py
│       │   ├── logs.py
│       │   ├── agent.py
│       │   ├── analyze.py
│       │   └── incidents.py
│       └── middleware.py          # request_id, logging
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_tools_system.py
│   │   ├── test_tools_infrastructure.py
│   │   ├── test_tools_logs.py
│   │   ├── test_anomaly.py
│   │   └── test_api.py
│   └── integration/
│       └── test_agent_workflow.py
└── docs/
    ├── ARCHITECTURE.md
    ├── IMPLEMENTATION_PLAN.md
    └── TOOLS.md
```

## Tool Definitions

See `docs/TOOLS.md` for full schemas. Summary:

| Tool | Input | Output model |
|------|-------|--------------|
| `get_cpu_metrics` | — | `{cpu_percent, per_cpu, load_avg}` |
| `get_memory_metrics` | — | `{used, available, percent, total}` |
| `get_disk_metrics` | `mountpoint?` | `{partitions: [{device, usage, free}]}` |
| `get_network_metrics` | — | `{bytes_sent, bytes_recv, connections}` |
| `get_process_metrics` | `limit=10` | `{processes: [{pid, name, cpu, memory}]}` |
| `get_uptime_metrics` | — | `{uptime_seconds, boot_time, load_avg}` |
| `check_ping` | `host` | `{host, latency_ms, reachable}` |
| `check_http_health` | `url` | `{url, status, response_time_ms, healthy}` |
| `scan_port` | `host, port` | `{host, port, open}` |
| `check_ssl_certificate` | `hostname` | `{hostname, expires, days_remaining, valid}` |
| `resolve_dns` | `hostname` | `{hostname, addresses, resolved}` |
| `check_service_health` | `service_name` | `{name, running, status}` |
| `check_database` | — | `{connected, latency_ms, error?}` |
| `analyze_logs` | `path, lines=500` | `{errors, patterns, summary}` |

All tools return `ToolResult[T]` with `{success, data, error, executed_at}`.

## Development Roadmap

| Phase | Scope | Deliverables |
|-------|-------|--------------|
| **1** | Monitoring tools | All tools, models, unit tests |
| **2** | API layer | FastAPI routes, middleware, API tests |
| **3** | Agent reasoning | ADK agent, prompts, executor, /agent/query |
| **4** | Memory & history | SQLite, incidents, /incidents |
| **5** | Dashboard | React or Streamlit MVP |
| **6** | Advanced AI | Eval dataset, anomaly trends, notifications stub |

## Phase 1 Tasks (current)

1. `pyproject.toml` with dependencies
2. Config + structured logging
3. Pydantic models for all tool outputs
4. Implement tools (system, infrastructure, services, logs)
5. Unit tests with mocks for edge cases

## Assumptions

- Monitors the **local host** where the agent runs (multi-server in future)
- Log paths and HTTP endpoints configured via `.env` / `settings.py`
- Gemini API key via `GOOGLE_API_KEY` or Vertex (`GOOGLE_CLOUD_PROJECT`)
- Database check uses configurable connection string (SQLite default for demo)
- Windows-compatible (psutil works cross-platform; ping uses subprocess fallback)
