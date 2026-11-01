# Capability: sources api

### Requirement: Test a connection without creating a source
The `api` service SHALL expose `POST /sources/test-connection`, calling the registered `Harvester.connect()` for the given `type`/`uri`/`credentials_ref` and returning `{ok, error}`; the credential value itself SHALL never be echoed back in the response.

#### Scenario: connect succeeds
- **Given** a known source type and a `connect()` that returns `ok=True`
- **When** `POST /sources/test-connection` is called
- **Then** the response is `200` with `ok=true` and no credential value in the body

#### Scenario: connect fails
- **Given** a `connect()` that returns `ok=False` with an error
- **When** `POST /sources/test-connection` is called
- **Then** the response is `200` with `ok=false` and that error message, and still no credential value in the body

### Requirement: Discover a source's scope tree
The `api` service SHALL expose `POST /sources/{id}/discover`, calling the source's registered harvester's `connect()` then `discover()` and returning the resulting `ScopeTree` as a nested tree of nodes with id, kind, name and size hint.

#### Scenario: discover returns the scope tree
- **Given** a source whose harvester discovers a `ScopeTree`
- **When** `POST /sources/{id}/discover` is called
- **Then** the response body matches the `ScopeTree` shape with nested nodes

#### Scenario: unknown source
- **Given** no source exists with the given id
- **When** `POST /sources/{id}/discover` is called
- **Then** the response is `404`

### Requirement: Preview the harvest plan for a selected scope
The `api` service SHALL expose `POST /sources/{id}/plan`, accepting an optional list of selected scope-tree leaf refs, calling `profile()` then `plan()` over that selection (or the full discovered scope when no selection is given), and returning the resulting `HarvestPlan`, the `Profile`, byte/file/time/token estimates derived from the profile, and a list of budget-warning strings whenever an estimate exceeds the plan's own budgets.

#### Scenario: plan preview with estimates
- **Given** a profiled plan
- **When** `POST /sources/{id}/plan` is called
- **Then** the response includes the plan's `include`/`exclude`/budgets, the profile's `object_count`/`total_bytes`/`counts_by_type`, and byte/file/time/token estimates

#### Scenario: budget warning
- **Given** a profiled plan whose estimated bytes exceed `budgets.max_bytes`
- **When** `POST /sources/{id}/plan` is called
- **Then** the response includes a non-empty `budget_warnings` list naming the exceeded budget

### Requirement: Start, read and stop a harvest run
The `api` service SHALL expose `POST /sources/{id}/runs` (inserts a `harvest_runs` row in state `APPROVED` with the given plan JSON and returns its id/source_id/state), `GET /runs/{id}` (returns id, source_id, state, plan, a manifest summary — discovered/fetched/skipped/failed counts plus total fetched bytes — a per-object log derived from the manifest, and error), and `PATCH /runs/{id}/stop` (sets a non-terminal run's state to `FAILED` with `error="stopped by user"`; this is an API-level state change only — it does not and cannot kill an already-running harvester container, since no job-control mechanism exists for that).

#### Scenario: create a run
- **Given** a valid plan body and an existing source
- **When** `POST /sources/{id}/runs` is called
- **Then** a `harvest_runs` row is created in state `APPROVED` and its id/source_id/state are returned

#### Scenario: read a run's status
- **Given** a `harvest_runs` row with a manifest of discovered/fetched/skipped entries
- **When** `GET /runs/{id}` is called
- **Then** the response includes the run's state, its plan, a manifest summary (including total fetched bytes) and a log entry per manifest record

#### Scenario: stop a non-terminal run
- **Given** a run in state `HARVESTING`
- **When** `PATCH /runs/{id}/stop` is called
- **Then** its state becomes `FAILED` with `error="stopped by user"`

#### Scenario: stop a terminal run
- **Given** a run already in state `PUBLISHED`, `QUARANTINED`, `FAILED` or `PARTIAL`
- **When** `PATCH /runs/{id}/stop` is called
- **Then** the response is `409` and the state is unchanged

### Requirement: Validation report endpoint
The `api` service SHALL expose `GET /runs/{id}/validation`, returning the `harvest_runs.report` column's JSON (`{status, checks: [{name, status, message, counts, samples}]}`) when present, or `404` when the run has no report yet. A migration (`0005_harvest_runs_report`) adds the nullable `harvest_runs.report JSONB` column (see CLAUDE.md's Postgres schema v0).

#### Scenario: report present
- **Given** a `harvest_runs` row with a populated `report` column
- **When** `GET /runs/{id}/validation` is called
- **Then** the response is `200` with that report shape

#### Scenario: report not yet available
- **Given** a run whose `report` column is still `NULL`
- **When** `GET /runs/{id}/validation` is called
- **Then** the response is `404`

### Requirement: Graph query endpoint
The `api` service SHALL expose `GET /graph`, returning `{nodes, edges}` from the `entities`/`edges` tables, filterable by `source_id`, `type` (entity type) and `relation` (edge relation) query parameters, excluding tombstoned entities and any edge whose endpoint is not in the returned node set.

#### Scenario: filtered graph query
- **Given** entities of two types for a source
- **When** `GET /graph?source_id=...&type=Repository` is called
- **Then** only matching, non-tombstoned entities and the edges between returned nodes are included

### Notes
- Run status is polling-based (`GET /runs/{id}` on an interval); no push/streaming transport exists, a deliberate hackathon-minimal choice over SSE/websockets.
- `Harvester.validate()`'s declared contract (`harvesters/base.py`) returns `status`/`checks: dict[str, str]`/`errors` only — never per-check counts/samples. The richer `harvest_validation.report.ValidationReport` (with `CheckResult.counts`/`samples`) exists but nothing in the harvester lifecycle populates it onto a `harvest_runs` row today, so `report` stays `NULL` for any run driven through the real `harvesters/run.py` runner until a future story unifies the two shapes or a harvester's `validate()` is changed to populate it. Not fixed here: it would mean changing the protected `Harvester` interface in `CLAUDE.md`.
- Git harvester `normalize()`/`validate()` still raise `NotImplementedError` (pre-existing, KAN-78/79/80 scope), so a real end-to-end `git` run started via `POST /sources/{id}/runs` reaches `HARVESTING` then fails at `normalize()`; no live run can reach `PUBLISHED`/`QUARANTINED` with a populated `report` yet.
- `list`/`create` sources (`GET`/`POST /sources`) are specified in `spec/capabilities/source-registry.md`; this capability only adds the endpoints above.
- Reconciling the provisional `dispatcher_runs` table (`spec/capabilities/dispatcher.md`) with `harvest_runs` is an open question, not addressed here.
