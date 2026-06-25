# Server Health Monitoring Agent

AI-powered server health monitoring assistant for the **5-Day Google AI Agents Capstone**.

Operators face noisy alerts, fragmented metrics, and slow root-cause analysis. This agent observes real server signals, correlates evidence deterministically, and returns structured explanations with confidence scores and remediation recommendations — without fabricating metrics.

## Problem Statement

When server performance degrades, teams must quickly answer: *What is happening? How confident are we? What should we do next?* Traditional dashboards show numbers but not narrative reasoning. Manual triage across CPU, memory, logs, and database checks is slow and error-prone.

## Business Value

| Benefit | How the agent delivers |
|---------|------------------------|
| Faster MTTR | Correlates CPU, memory, logs, and DB signals in one query |
| Trustworthy answers | Facts come from deterministic tools, not LLM guesses |
| Institutional memory | SQLite stores incidents and metric history for trend analysis |
| Extensibility | MCP exposes tools to Antigravity, Cursor, and other MCP clients |
| Deployability | Docker Compose stack with health checks and persistent storage |

## Architecture

```
Client (React / REST / MCP)
        │
        ▼
   FastAPI API Layer
        │
   ┌────┴────┐
   ▼         ▼
 ADK Agent   Services (history, incidents, correlation)
   │         │
   └────┬────┘
        ▼
  Tool Registry → Deterministic Tools (psutil, logs, DB)
        │
        ▼
     SQLite
```

Detailed diagrams: [docs/architecture_diagram.md](docs/architecture_diagram.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### Components

| Layer | Responsibility |
|-------|----------------|
| **Tools** | Deterministic metric collection (`backend/tools/`) |
| **Tool Registry** | Discovery, metadata, execution (`backend/services/tool_registry.py`) |
| **MCP Server** | stdio transport for external agents (`backend/mcp/`) |
| **ADK Agent** | Planning, tool execution, reasoning, structured responses |
| **Services** | History, incidents, correlation, anomaly detection |
| **Dashboard** | React UI for metrics, trends, incidents |

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ (for dashboard)

### Install

```bash
uv sync --extra dev
cp .env.example .env
# Set GOOGLE_API_KEY in .env for agent queries
```

### Run API

```bash
# Preferred on Windows (paths with spaces) and all platforms:
uv run python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Windows helper script:
.\scripts\run_api.ps1
```

> **Note:** `uv run uvicorn ...` may fail on Windows if the project path contains spaces (e.g. `Personal Folder`). Use `python -m uvicorn` instead.

### Run Dashboard

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

### Run Tests

```bash
uv run pytest -v
```

## MCP Server

Expose monitoring tools over stdio for Antigravity / Cursor / Claude Desktop:

```bash
uv run python -m backend.mcp.mcp_server
```

**Exposed tools:** `get_cpu_metrics`, `get_memory_metrics`, `get_disk_metrics`, `analyze_logs`, `get_history`, `get_incidents`, `check_database`

All tools route through the existing tool registry or service adapters with JSON schema metadata. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for MCP client configuration.

## Docker Deployment

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/health |

SQLite data persists in the `sqlite_data` Docker volume. Full guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Demo Scenarios (Antigravity Video)

Seed realistic demo data for recording:

```bash
uv run python scripts/demo/run_all.py
```

| Scenario | Script | Demo prompt |
|----------|--------|-------------|
| CPU spike | `scenario_01_cpu_spike.py` | "Why is CPU utilization spiking?" |
| Memory leak | `scenario_02_memory_leak.py` | "Is there a memory leak?" |
| DB latency | `scenario_03_db_latency.py` | "Check database latency trends" |
| Incident correlation | `scenario_04_incidents_correlation.py` | `GET /correlation?window_hours=1` |

Recording guide: [docs/demo_script.md](docs/demo_script.md) · [docs/video_outline.md](docs/video_outline.md)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | API and database health |
| GET | `/metrics` | Live system metrics snapshot |
| GET | `/logs` | Log analysis |
| POST | `/agent/query` | Natural language query |
| POST | `/analyze` | Full health analysis |
| GET | `/history` | Metric snapshot history |
| GET | `/history/trends` | Trend analysis |
| GET | `/incidents` | Historical incidents |
| GET | `/correlation` | Incident correlation patterns |

## Screenshots & Diagrams

| Asset | Location |
|-------|----------|
| Architecture diagram | [docs/architecture_diagram.md](docs/architecture_diagram.md) |
| Tool schemas | [docs/TOOLS.md](docs/TOOLS.md) |
| Implementation plan | [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) |
| Judge checklist | [docs/judge_checklist.md](docs/judge_checklist.md) |

> Add dashboard screenshots to `docs/screenshots/` before final Kaggle submission.

## Evaluation

```bash
uv run python -m backend.evaluations.runner
```

## Agent Rules

- Never fabricate metrics
- Distinguish facts vs inferences
- Return confidence scores and severity levels
- State "I could not obtain sufficient evidence" when tools fail

## Development Phases

| Phase | Status |
|-------|--------|
| 1 — Monitoring tools | Complete |
| 2 — API layer | Complete |
| 3 — Agent reasoning | Complete |
| 4 — Memory groundwork | Complete |
| 5 — Historical intelligence | Complete |
| 6 — Evaluation framework | Complete |
| 7 — Security hardening | Complete |
| 8 — React dashboard | Complete |
| 9 — Optional LLM enhancement | Complete |
| 10 — MCP + Docker + Demo assets | Complete |

## Future Improvements

- Slack/email/Telegram alerts
- Kubernetes and Docker container monitoring
- Multi-server fleet support
- Cloud SQL / managed database backend
