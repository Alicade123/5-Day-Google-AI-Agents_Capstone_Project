# Deployment Guide — Server Health Monitoring Agent

## Local Docker Deployment

### Prerequisites

- Docker Engine 24+
- Docker Compose v2
- Copy `.env.example` to `.env` and set `GOOGLE_API_KEY` if using agent queries

### Start the stack

```bash
cp .env.example .env
docker compose up --build
```

| Service  | URL                         |
|----------|-----------------------------|
| Frontend | http://localhost:5173       |
| Backend  | http://localhost:8000       |
| Health   | http://localhost:8000/health |

The `sqlite_data` volume persists incidents and metric history across restarts.

### Environment variables

Key variables (see `.env.example` for the full list):

| Variable       | Default                              | Purpose                    |
|----------------|--------------------------------------|----------------------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/incidents.db` | SQLite persistence path |
| `API_KEY`      | empty                                | Optional API auth          |
| `CORS_ORIGINS` | localhost dashboard origins          | CORS allowlist             |
| `LOG_PATHS`    | empty                                | Log files for analysis     |

### Health checks

- **Backend**: `GET /health` — verifies SQLite incident and history stores
- **Frontend**: nginx serves the built React dashboard

### Stop and clean up

```bash
docker compose down          # keep volume
docker compose down -v         # remove SQLite volume
```

---

## MCP Server (stdio)

Run the MCP server for Antigravity / Claude Desktop / Cursor integration:

```bash
uv run python -m backend.mcp.mcp_server
```

Exposed tools: `get_cpu_metrics`, `get_memory_metrics`, `get_disk_metrics`, `analyze_logs`, `get_history`, `get_incidents`, `check_database`.

Example Cursor MCP config:

```json
{
  "mcpServers": {
    "server-health-agent": {
      "command": "uv",
      "args": ["run", "python", "-m", "backend.mcp.mcp_server"],
      "cwd": "/path/to/Capstone_Project"
    }
  }
}
```

---

## Demo Data (Antigravity video)

Seed all four demo scenarios:

```bash
uv run python scripts/demo/run_all.py
```

Individual scenarios:

```bash
uv run python scripts/demo/scenario_01_cpu_spike.py
uv run python scripts/demo/scenario_02_memory_leak.py
uv run python scripts/demo/scenario_03_db_latency.py
uv run python scripts/demo/scenario_04_incidents_correlation.py
```

---

## Optional Cloud Deployment (Google Cloud Run)

### Backend

```bash
gcloud run deploy server-health-backend \
  --source . \
  --dockerfile Dockerfile.backend \
  --port 8000 \
  --set-env-vars "LOG_LEVEL=INFO" \
  --allow-unauthenticated
```

> Cloud Run is stateless. Mount Cloud SQL or use a persistent volume strategy for production SQLite, or switch `DATABASE_URL` to a managed database.

### Frontend

Build and deploy the nginx image separately, setting the API proxy target to the Cloud Run backend URL in `frontend/nginx.conf`, or serve the frontend from the same origin via a reverse proxy.

### Secrets

Store `GOOGLE_API_KEY` and `API_KEY` in Secret Manager and reference them as environment variables in Cloud Run.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Backend unhealthy on start | Wait for `start_period`; check `docker compose logs backend` |
| Dashboard cannot reach API | Ensure frontend nginx proxies `/api/` to `backend:8000` |
| Empty history/incidents | Run demo seed scripts or call `POST /analyze` to collect snapshots |
| MCP tools return errors | Run from project root so `backend` package resolves |
