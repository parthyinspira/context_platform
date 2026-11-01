# Verification (lite)

Status: PASS
Date: 2026-10-31   Commit: 1fefb23d (pre-commit; see branch m8-ui-wizard-and-runs)

| Acceptance criterion | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Endpoints for list/create sources | Pre-existing (`api/tests/test_sources.py`), reused unchanged | PASS |
| Start run | `api/tests/test_runs.py::test_create_run_then_get_returns_detail`, `::test_create_run_unknown_source_returns_404` | PASS |
| Run status (poll-based "stream") | `api/tests/test_runs.py::test_create_run_then_get_returns_detail` (GET /runs/{id}) | PASS |
| Plan preview | `api/tests/test_discovery.py::test_plan_returns_estimates_from_profile`, `::test_plan_reports_budget_warning_when_estimate_exceeds_budget` | PASS |
| Validation report | `api/tests/test_runs.py::test_get_validation_report_present`, `::test_get_validation_report_missing_returns_404` | PASS |
| Graph query (nodes/edges with filters) | `api/tests/test_graph.py::test_graph_filters_by_source_and_type`, `::test_graph_excludes_tombstoned_entities_and_their_edges` | PASS |
| Documented | OpenAPI `summary`/`description` added to every new route (`api/app/routes_discovery.py`, `routes_runs.py`); auto-served at `/docs` | PASS |

Supporting: `python -m pytest api/tests -q` → 42 passed (16 new). `python -m pytest scheduler/tests harvesters harvest_validation -q` → unaffected (8 / 127 / 68 passed).

Not verified: live Postgres migration apply (`0005_harvest_runs_report`) and a real end-to-end `git` harvest run — deferred to the bundle's one `docker compose up` check (lite mode, run once per bundle, not per story); git harvester `normalize()`/`validate()` are pre-existing `NotImplementedError`s so no live demo run can reach PUBLISHED/QUARANTINED with a populated `report` yet (see plan.md Risks).
