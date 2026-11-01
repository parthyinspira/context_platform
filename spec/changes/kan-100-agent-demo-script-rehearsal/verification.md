# KAN-100 verification (lite)

Status: PASS

| AC | Scenario | Evidence | Result |
|---|---|---|---|
| 1. Scripted demo of all four agents | A: workflow agent returns downstream assets (REVENUE_DAILY, dash-revenue) and owners | `test_downstream_assets_found` PASS; answer includes "Affected assets" with citations | PASS |
| 1. Scripted demo of all four agents | B: research agent flags false Kafka claim as UNVERIFIED | `test_false_claim_flagged` PASS; "UNVERIFIED" in answer | PASS |
| 1. Scripted demo of all four agents | C: prod-support agent ranks etl_weekly_transform as top cause | `test_broken_job_in_top_causes` PASS; `test_broken_job_node_retrieved` PASS | PASS |
| 1. Scripted demo of all four agents | D: call-centre agent answers in-scope, escalates out-of-scope, no restricted content | `test_in_scope_returns_answer`, `test_out_of_scope_escalates`, `test_no_restricted_content_for_internal_caller` PASS | PASS |
| 2. Graph trace overlay | GraphCanvas accepts `agentTrace` prop; matching nodes get `.agent-retrieved` class with amber border and retrieval-order badge | Code inspection: `GraphCanvas.jsx` applies class + style; overlay effect wired via `useEffect` on `agentTrace` | PASS (structural; browser render not tested) |

## Tests run
```
agents/tests/test_agents.py — 17 passed, 0 failed
```

## Checks
- `secret-scan`: no secrets found
- `spec_check`: OK (lite plan)
- No Docker compose run required (no service/compose changes)
- `contract-check`: agents endpoint added to API (routes_agents.py); no schema/ontology/harvester interface changes

## Not verified here
- Live graph overlay animation (amber pulse) — requires browser; structural class application is verified by code review.
- `POST /agents/{name}/run` endpoint with a running API service — agents module imports work correctly (confirmed by unit tests using same Python path as the router).
