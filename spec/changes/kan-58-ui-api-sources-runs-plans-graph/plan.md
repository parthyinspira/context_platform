# KAN-58: UI API for sources, runs, plans and graph queries (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-58   Branch: m8-ui-wizard-and-runs

## Scope
In: new FastAPI routes in `api/` composing existing harvester-framework types over `harvest_runs`: test-connection, discover, plan preview, create/read/stop a run, validation report, graph query. A small migration adds `harvest_runs.report JSONB` to hold a structured validation report when a harvester supplies one.
Out: `list/create sources` (already done, B2 — not touched beyond reuse); real-time push (status is polled, not SSE/websocket, for hackathon minimalism); reconciling `dispatcher_runs` with `harvest_runs` (flagged as open question, left to a future story); git harvester `normalize()`/`validate()` (still `NotImplementedError`, pre-existing and out of scope here); auth/authz.

## Acceptance criteria (from Jira)
1. Endpoints for list/create sources (existing), start run, run status (poll-based "stream"), plan preview, validation report, graph query (nodes/edges with filters).
2. Documented (OpenAPI summaries/docstrings on each new route; FastAPI auto-serves `/docs`).

## Requirements (at most 5)
- The `api` service SHALL expose `POST /sources/test-connection` that calls the registered `Harvester.connect()` for the given `type`/`uri`/`credentials_ref` and returns `{ok, error}`, never echoing the credential value itself. (scenario: Given a known source type and a connect() that returns ok=True, When POST /sources/test-connection is called, Then the response is 200 with ok=true and no credential value in the body; Given connect() returns ok=False with an error, Then the response is 200 with ok=false and that error message)
- The `api` service SHALL expose `POST /sources/{id}/discover` (calls `connect()`+`discover()`, returns the `ScopeTree`) and `POST /sources/{id}/plan` (calls `profile()`+`plan()` over an optional list of selected refs, returns the `HarvestPlan`, a `Profile`-derived estimate of bytes/files, and a list of budget-warning strings when the plan's budgets would be exceeded by the profiled size). (scenario: Given a source whose harvester discovers a ScopeTree, When POST /sources/{id}/discover is called, Then the response body matches the ScopeTree shape with nested nodes; Given a profiled plan whose estimated bytes exceed `budgets.max_bytes`, When POST /sources/{id}/plan is called, Then the response includes a non-empty `budget_warnings` list)
- The `api` service SHALL expose `POST /sources/{id}/runs` (inserts a `harvest_runs` row in state `APPROVED` with the given plan JSON, returns id/source_id/state), `GET /runs/{id}` (returns id, source_id, state, plan, manifest summary via `Manifest.counts()`-shaped data, error), and `PATCH /runs/{id}/stop` (sets a non-terminal run's state to `FAILED` with `error="stopped by user"`; 409 if the run is already terminal). (scenario: Given a valid plan body, When POST /sources/{id}/runs is called, Then a harvest_runs row is created in state APPROVED and returned; Given a run in state HARVESTING, When PATCH /runs/{id}/stop is called, Then its state becomes FAILED with that error; Given a run already PUBLISHED, When PATCH /runs/{id}/stop is called, Then the response is 409 and the state is unchanged)
- The `api` service SHALL expose `GET /runs/{id}/validation` returning the `report` column's JSON (`{status, checks:[{name,status,message,counts,samples}]}`) when present, or 404 when the run has no report yet. A migration adds the nullable `harvest_runs.report JSONB` column. (scenario: Given a harvest_runs row with a populated `report` column, When GET /runs/{id}/validation is called, Then the response is 200 with that report shape; Given a run with `report` still NULL, When the endpoint is called, Then the response is 404)
- The `api` service SHALL expose `GET /graph` returning `{nodes, edges}` from the `entities`/`edges` tables, filterable by `source_id`, `type` (entity type) and `relation` (edge relation) query parameters, excluding tombstoned entities. (scenario: Given entities of two types for a source, When GET /graph?source_id=...&type=Repository is called, Then only matching, non-tombstoned entities and the edges between returned nodes are included)

## Tasks
- [x] 1. Migration `0005_harvest_runs_report` adding nullable `report JSONB` to `harvest_runs` (test: up/down apply cleanly)
- [x] 2. `POST /sources/test-connection` route + schema (tests: ok case, connect-failure case)
- [x] 3. `POST /sources/{id}/discover` and `POST /sources/{id}/plan` routes (tests: discover shape, plan budget-warning case)
- [x] 4. `POST /sources/{id}/runs`, `GET /runs/{id}`, `PATCH /runs/{id}/stop` routes (tests: create, stop-success, stop-on-terminal-409)
- [x] 5. `GET /runs/{id}/validation` route (tests: report-present, report-missing-404)
- [x] 6. `GET /graph` route (tests: filtered query, tombstoned exclusion)
- [x] 7. Add route docstrings/summaries for OpenAPI (done); the `spec/capabilities/sources-api.md` capability delta is applied once for the whole bundle during the bundle-wide `spec-archive` pass (lite mode), not per story

## Risks / not verifiable here
- `Harvester.validate()`'s declared contract (`harvesters/base.py`) returns `status`/`checks: dict[str,str]`/`errors` only — never per-check counts/samples. The richer `harvest_validation.report.ValidationReport` (with `CheckResult.counts`/`samples`) exists but nothing in the harvester lifecycle populates it onto a `harvest_runs` row today; this is a pre-existing gap flagged in `harvest_validation/validator.py`'s own docstring, not something this story fixes (would mean changing the protected `Harvester` interface in `CLAUDE.md`). `report` will stay NULL for any run driven through the real `harvesters/run.py` runner until a future story unifies the two shapes or a harvester's `validate()` is changed to populate it; verified here only against a seeded/mocked `report` value.
- Git harvester `normalize()`/`validate()` still raise `NotImplementedError`, so a real end-to-end `git` run started via the new `POST /sources/{id}/runs` will reach `HARVESTING` then fail at `normalize()` — this is pre-existing (KAN-78/79/80 scope), not introduced or fixed here.
- No live Postgres/Docker in per-story tests (per lite mode); DB behaviour verified with fake cursor/connection doubles as the existing `api/tests/test_sources.py` pattern does. Real migration apply is checked once at the bundle's `docker compose up` step.

## Approval
Approved by: parthasarathy.venkatachalam (user approved spec-batch), 2026-10-31
