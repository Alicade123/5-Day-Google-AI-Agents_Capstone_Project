# Evaluation Framework

Agent behavior evaluation — separate from pytest LLM assertions.

## Run evaluation

```bash
uv run python -m backend.evaluations.runner
```

Or via API:

```bash
curl -X POST http://localhost:8000/eval/run
```

## Metrics

| Metric | Description |
|--------|-------------|
| factual_grounding | Facts traceable to tool outputs |
| tool_selection_correctness | Planner selects expected tools |
| response_completeness | All response sections present |
| hallucination_detection | No numbers absent from evidence |
| latency | Response within time budget |

## Dataset

Edit `datasets/default.json` to add cases. Configure thresholds in `eval_config.yaml`.

## Design

- Pytest tests deterministic graders only (`tests/unit/test_eval_metrics.py`)
- Full agent eval uses `EvalRunner` with orchestrator pipeline
- Does NOT assert on LLM prose quality — use `agents-cli eval` for that in production
