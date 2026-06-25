# Demo Script — Antigravity Video Recording

Use this script when recording the capstone demonstration video.

## Pre-recording Setup (5 min)

```bash
uv sync --extra dev
cp .env.example .env
# Set GOOGLE_API_KEY in .env

# Terminal 1 — API
uv run python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Dashboard
cd frontend && npm install && npm run dev

# Terminal 3 — Seed demo data
uv run python scripts/demo/run_all.py
```

Open http://localhost:5173

---

## Scene 1 — Introduction (30 sec)

**Say:** "This is the Server Health Monitoring Agent — an AI assistant that observes real server metrics, correlates evidence, and returns structured explanations with confidence scores. It never fabricates data."

**Show:** Dashboard loading with live metrics from `GET /metrics`.

---

## Scene 2 — CPU Spike (1 min)

**Say:** "Let's investigate a CPU spike scenario."

**Do:**
1. Run (or confirm) `uv run python scripts/demo/scenario_01_cpu_spike.py`
2. Refresh dashboard — point out rising CPU trend chart
3. Ask agent: **"Why is CPU utilization spiking?"**
4. Highlight **Facts**, **Confidence**, and **Recommended actions** in the response

**Show API:** `GET /history/trends?window_minutes=15`

---

## Scene 3 — Memory Leak (1 min)

**Say:** "Next, a sustained memory increase pattern."

**Do:**
1. Run `uv run python scripts/demo/scenario_02_memory_leak.py`
2. Show memory trend increasing across observations
3. Ask: **"Is there a memory leak on this server?"**

---

## Scene 4 — Database Latency (1 min)

**Say:** "Database latency often correlates with resource pressure."

**Do:**
1. Run `uv run python scripts/demo/scenario_03_db_latency.py`
2. Call `GET /metrics` or use MCP tool `check_database`
3. Ask: **"Check database connectivity and explain latency trends"**

---

## Scene 5 — Repeated Incidents Correlation (1 min)

**Say:** "The agent remembers past incidents and detects recurring patterns."

**Do:**
1. Run `uv run python scripts/demo/scenario_04_incidents_correlation.py`
2. Open **Incidents** panel on dashboard
3. Show `GET /correlation?window_hours=1` — highlight repeated CPU/DB patterns

---

## Scene 6 — MCP Integration (45 sec)

**Say:** "Tools are also exposed via MCP for external agent clients."

**Do:**
1. Show `backend/mcp/mcp_server.py` briefly in IDE
2. Mention tools: `get_cpu_metrics`, `get_memory_metrics`, `get_disk_metrics`, `analyze_logs`, `get_history`, `get_incidents`, `check_database`
3. Optional: invoke one tool from Antigravity / Cursor MCP panel

---

## Scene 7 — Deployment (30 sec)

**Say:** "The project ships with Docker Compose for one-command deployment."

**Do:**
```bash
docker compose up --build
```

Show http://localhost:5173 and http://localhost:8000/health

---

## Closing (15 sec)

**Say:** "The agent combines deterministic monitoring tools, Google ADK reasoning, historical intelligence, and MCP interoperability — ready for operators who need trustworthy, explainable server health insights."
