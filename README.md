# Server Health Monitoring Agent

AI-powered server health monitoring assistant for the **5-Day Google AI Agents Capstone**.

## Overview

Observes system metrics, service health, infrastructure endpoints, and logs; reasons over evidence; and returns structured explanations with confidence scores and remediation recommendations.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Setup

```bash
uv sync --extra dev
cp .env.example .env
```

## Run API

```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Run Tests

```bash
uv run pytest -v
```

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

## Dashboard

```bash
# Terminal 1: API
uv run uvicorn backend.main:app --reload --port 8000

# Terminal 2: Dashboard
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

## Evaluation

```bash
uv run python -m backend.evaluations.runner
```

## API

- `GET /health` — API health
- `GET /metrics` — System metrics snapshot
- `GET /logs` — Log analysis
- `POST /agent/query` — Natural language query (`{"query": "..."}`)
- `POST /analyze` — Full health analysis
- `GET /history` — Historical metric snapshots
- `GET /history/trends` — Trend analysis and moving averages
- `GET /correlation` — Incident correlation patterns
- `GET /incidents` — Historical incidents

## Agent Rules

- Never fabricate metrics
- Distinguish facts vs inferences
- Return confidence scores and severity levels

## Future Improvements

- Slack/email/Telegram alerts
- Kubernetes and Docker monitoring
- Multi-server fleet support
- React dashboard
"# 5-Day-Google-AI-Agents_Capstone_Project" 
