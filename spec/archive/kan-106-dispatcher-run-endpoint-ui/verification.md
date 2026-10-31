# Verification

Status: PASS

## Checks
- `python -m pytest scheduler/tests -q` -> 8 passed (`scheduler/tests/test_dispatcher.py`, `scheduler/tests/test_health.py`)
- `python -m pytest api/tests -q` -> 18 passed (unchanged; confirms no regression)
- `python -m ruff check scheduler --config pyproject.toml` -> All checks passed
- `secret-scan` skill -> no secrets found; `.env` untracked (`git ls-files` shows only `.env.example`); the one `password=`-shaped match in the diff is the pre-existing `change-me` placeholder default already used by the `api` service
- `contract-check` skill -> no mismatches; `dispatcher_runs` is a new table with a migration (0003), flagged in `proposal.md` as a deliberate, documented provisional addition (not a silent contract change); no cloud SDK imports added outside `adapters/`
- `python scripts/spec_check.py spec/changes/kan-106-dispatcher-run-endpoint-ui` -> OK (plan)
- `python scripts/spec_check.py spec/changes/kan-106-dispatcher-run-endpoint-ui --stage=verify` -> OK (verify, after this file was added and all tasks ticked)

## Scenario evidence
- **run-active-source** (`specs/dispatcher.md` "run an active source"): `scheduler/tests/test_dispatcher.py::test_run_active_source_queues_run_and_publishes_event` — asserts `201`, run id/source id/status `queued` in the body, a `dispatcher_runs` row recorded, `conn.commit()`/`conn.close()` called, and `harvest.requested` published with matching `run_id`/`source_id`/`source_type`.
- **run-unknown-source** (`specs/dispatcher.md` "run an unknown source"): `test_run_unknown_source_returns_404` — asserts `404`, no run recorded, no event published.
- **run-inactive-source** (`specs/dispatcher.md` "run an inactive source"): `test_run_inactive_source_returns_409` — source with status `paused`, asserts `409`, no run recorded, no event published.
- **due-sources-never-harvested** (`specs/dispatcher.md` "never-harvested source is due"): `test_due_sources_includes_never_harvested_active_source` — `last_harvest_at=None` source appears in `GET /sources/due`.
- **due-sources-excludes-recent** (`specs/dispatcher.md` "recently harvested source is not due"): `test_due_sources_excludes_recently_harvested_source` — yearly cron schedule harvested 1 minute ago is excluded.
- **due-sources-includes-elapsed** (`specs/dispatcher.md` "source past its schedule is due"): `test_due_sources_includes_source_past_its_schedule` — every-5-minutes cron schedule harvested 1 hour ago is included.
- **due-sources-excludes-inactive** (`specs/dispatcher.md` "inactive sources are excluded"): `test_due_sources_excludes_inactive_sources` — paused source with no harvest history is excluded from `GET /sources/due` even though it would otherwise be "never harvested".

## Acceptance criteria
Jira AC (verbatim): "POST /sources/{id}/run starts the harvest lifecycle and returns run id; polling registry for due sources; no Airflow."

1. **`POST /sources/{id}/run` starts the harvest lifecycle and returns a run id** — PASS. Evidence: run-active-source, run-unknown-source, run-inactive-source scenarios above. "Starts the harvest lifecycle" is scoped (per `proposal.md` "Out of scope") to recording the run and publishing `harvest.requested`; it does not launch a harvester container, since no harvester container exists yet in this codebase (later epics) and the full `harvest_runs` lifecycle table is explicitly scoped to the later harvest-core epic (B4, `docs/MILESTONES.md`).
2. **Polling registry for due sources** — PASS. Evidence: the four due-sources scenarios above exercise `GET /sources/due` against the `sources` registry directly (status + schedule + last_harvest_at).
3. **No Airflow** — PASS. Evidence: `grep -ri airflow` across the changed files and `scheduler/requirements.txt` returns no matches; the dispatcher is a plain FastAPI service per `docs/HACKATHON_SCOPE.md`.

## Not verified
- **Compose cron loop wiring.** No scheduled loop was added that actually polls `GET /sources/due` and calls `POST /sources/{id}/run` on a timer. The Jira AC says "polling registry for due sources", which `GET /sources/due` provides as a queryable surface; wiring an automatic timer loop around it is not named in the AC and is called out here as follow-up work, not silently skipped.
- **Live Postgres / `docker compose up` end-to-end run.** Tests use in-memory fakes for the DB connection and EventBus (same approach as `api/tests/test_sources.py`), matching this repo's existing test strategy; the migration was not applied against a live database in this session (no local Postgres instance was started for this change). The SQL was visually checked against `migrations/0001_core_tables.up.sql`'s conventions and the fakes assert the exact SQL shape used by the route.
- **Actual harvester execution following `harvest.requested`.** No consumer of `harvest.requested` exists yet (harvester containers are later epics); the event is published but nothing currently acts on it beyond the outbox record, which is expected at this stage of the build order.
