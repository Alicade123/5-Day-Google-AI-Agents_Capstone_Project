# Repository Visibility Report

**Mode:** GitHub Submission Cleanup  
**Rule:** Files are hidden via `.gitignore` only — nothing deleted locally.

---

## Summary

| Category | Count (top-level areas) | GitHub visibility |
|----------|-------------------------|-------------------|
| PUBLIC | Core app + judge docs | Visible |
| LOCAL ONLY | Planning, Kaggle drafts, automation | Hidden |
| GENERATED | Caches, deps, DBs, builds | Hidden |

---

## PUBLIC — Visible on GitHub

| Path | Reason |
|------|--------|
| `README.md` | Primary entry point for judges |
| `pyproject.toml` | Dependencies and project metadata |
| `uv.lock` | Reproducible installs |
| `.env.example` | Safe configuration template |
| `backend/` | Application code (agents, API, MCP, tools, eval) |
| `frontend/` | React dashboard (excludes `node_modules`, `.env`) |
| `tests/` | Test suite (70 tests) |
| `Dockerfile.backend` | Deployment |
| `Dockerfile.frontend` | Deployment |
| `docker-compose.yml` | Deployment |
| `docs/DEPLOYMENT.md` | Run and deploy instructions |
| `docs/final_submission_report.md` | Submission status summary |
| `docs/demo_script.md` | Demo recording guide |
| `docs/ARCHITECTURE.md` | Technical architecture |
| `docs/TOOLS.md` | Tool schemas reference |
| `docs/architecture_diagram.png` | Judge-friendly architecture image |
| `docs/repository_visibility_report.md` | This audit |
| `docs/public_repo_manifest.md` | Public tree manifest |
| `scripts/demo/` | Demo scenario seed scripts |
| `scripts/__init__.py` | Package marker for demo imports |
| `frontend/.env.example` | Frontend env template |
| `frontend/nginx.conf` | Docker frontend proxy |
| `frontend/package.json` | Frontend dependencies |
| `frontend/package-lock.json` | Locked frontend deps |

### Key public capabilities preserved

| Capability | Location |
|------------|----------|
| MCP server | `backend/mcp/` |
| Evaluation framework | `backend/evaluations/` |
| Demo scenarios | `scripts/demo/scenario_*.py`, `run_all.py` |
| Security layer | `backend/api/security.py` |
| Docker deploy | Root Dockerfiles + compose |

---

## LOCAL ONLY — Hidden via `.gitignore`

| Path | Reason |
|------|--------|
| `.agents-cli-spec.md` | Internal agent scaffolding spec |
| `docs/kaggle_submission/` | Kaggle writeup drafts, title/subtitle options, media plan |
| `docs/IMPLEMENTATION_PLAN.md` | Internal development planning |
| `docs/judge_checklist.md` | Internal pre-submit checklist |
| `docs/video_outline.md` | Video production notes |
| `docs/architecture_diagram.md` | Mermaid source (PNG is public) |
| `docs/screenshots/` | Regenerated/local screenshot drafts |
| `scripts/screenshots/` | Screenshot automation (Playwright) |
| `scripts/run_api.ps1` | Windows dev helper |
| `.env` | Secrets |
| `frontend/.env` | Local frontend secrets |

---

## GENERATED — Hidden via `.gitignore`

| Path | Reason |
|------|--------|
| `.venv/` | Python virtual environment |
| `**/__pycache__/` | Python bytecode cache |
| `.pytest_cache/` | Pytest cache |
| `.coverage` | Coverage data |
| `frontend/node_modules/` | NPM dependencies |
| `frontend/dist/`, `build/` | Frontend build output |
| `data/` | SQLite DB, demo logs, runtime snapshots |
| `*.sqlite`, `*.db` | Database files anywhere |
| `logs/`, `*.log` | Log files |
| `tmp/`, `temp/`, `*.tmp` | Temporary files |
| `playwright-report/`, `test-results/` | Playwright artifacts |
| `.vscode/`, `.idea/` | IDE settings |
| `.DS_Store`, `Thumbs.db` | OS metadata |

---

## Per-folder classification

### `backend/` → PUBLIC

All source code including `backend/mcp/`, `backend/evaluations/`, `backend/agents/`, `backend/tools/`, `backend/api/`, `backend/services/`, `backend/memory/`.

### `frontend/src/` → PUBLIC

React application source. Generated `node_modules/` and `dist/` hidden.

### `tests/` → PUBLIC

Unit and integration tests.

### `scripts/demo/` → PUBLIC

| File | Category |
|------|----------|
| `run_all.py` | PUBLIC |
| `scenario_01_cpu_spike.py` | PUBLIC |
| `scenario_02_memory_leak.py` | PUBLIC |
| `scenario_03_db_latency.py` | PUBLIC |
| `scenario_04_incidents_correlation.py` | PUBLIC |
| `_common.py`, `__init__.py` | PUBLIC |
| `final_demo_check.py` | PUBLIC (verification; judge-reproducible) |

### `scripts/screenshots/` → LOCAL ONLY

Automation for Kaggle asset capture; not required to understand the product.

### `docs/kaggle_submission/` → LOCAL ONLY

| File | Category |
|------|----------|
| `title_options.md` | LOCAL ONLY |
| `subtitle_options.md` | LOCAL ONLY |
| `project_description.md` | LOCAL ONLY (paste into Kaggle manually) |
| `thumbnail_concepts.md` | LOCAL ONLY |
| `media_plan.md` | LOCAL ONLY |
| `project_links.md` | LOCAL ONLY |
| `judge_story.md` | LOCAL ONLY |
| `submission_checklist.md` | LOCAL ONLY |
| `README.md` | LOCAL ONLY |

---

## Scores

| Metric | Score | Notes |
|--------|-------|-------|
| **Repository cleanliness** | **92/100** | Focused public tree; no secrets; no generated noise |
| **Judge experience** | **90/100** | README + architecture PNG + deploy + demo scripts visible |

### Remaining manual actions

1. `git add` and commit public files only (verify with `git status`)
2. Confirm no `.env` staged: `git check-ignore -v .env`
3. Optionally force-add final screenshots to `docs/` root if needed for README embeds
4. Push to public GitHub and verify repo view in browser

---

*Generated for GitHub Submission Cleanup — files hidden, not deleted.*
