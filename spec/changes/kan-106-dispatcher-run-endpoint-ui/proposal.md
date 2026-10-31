# KAN-106: Dispatcher run endpoint for the UI

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-106   Epic: 4 Scheduler and incremental harvest   Branch: kepler/kan-106-dispatcher-run-endpoint-ui

## Why
The `scheduler` service is currently a health-check stub (`GET /health` only). The UI's planned "Run" button per source (`docs/HACKATHON_SCOPE.md`) and any future compose cron loop both need a dispatcher endpoint that starts a harvest and a way to find which sources are due, without pulling in Airflow.

## What changes
- Add `dispatcher_runs` table (migration `0003`) to track requested runs: a minimal, provisional record — not the full `harvest_runs` lifecycle.
- Add `POST /sources/{id}/run` to the `scheduler` service: validates the source exists and is `active`, inserts a `dispatcher_runs` row, publishes `harvest.requested` on the `EventBus`, returns the run id.
- Add `GET /sources/due` to the `scheduler` service: lists active sources whose cron `schedule` is due given `last_harvest_at`.
- Scheduler container now builds with access to `adapters/` (build context changed from `./scheduler` to repo root + `scheduler/Dockerfile`, matching the `api` service) so it can reuse the `EventBus`/`SecretStore` adapters instead of duplicating them.

## In scope
- The two endpoints above, their schemas, the migration, and tests (fakes, no live Postgres, mirroring `api/tests/test_sources.py`).
- Reusing `adapters/factory.py` for `EventBus`/`SecretStore` exactly as `api/app/main.py` does.

## Out of scope
- Airflow — not used anywhere; the dispatcher stays a simple FastAPI container per `docs/HACKATHON_SCOPE.md` ("Dispatcher — simple container service, no Airflow").
- The full `harvest_runs` lifecycle table (CONNECTING/.../PUBLISHED/QUARANTONED/PARTIAL) from `spec/capabilities/harvester-framework.md` — that is scoped to the later harvest-core epic (`docs/MILESTONES.md` "B4 Harvest core | 75, 12, 76, 77, 85"). `dispatcher_runs` is a provisional, minimal stand-in; it is expected to be superseded or merged into `harvest_runs` when that epic lands.
- Actually launching a harvester container/process — no harvester containers exist yet (later epics). "Starts the harvest lifecycle" here means: validate + record the run + publish the event that a future harvester/consumer will act on.
- Wiring an actual compose cron loop that polls `GET /sources/due` and calls `POST /sources/{id}/run` on a timer — `GET /sources/due` is the polling surface the AC asks for; the scheduling loop itself is not named in this story's AC and is called out under "Not verified" in `verification.md`.
- UI changes (no "Run" button wired up) — not named in this story's AC; UI work is epic 6+.

## Acceptance criteria (from Jira)
"POST /sources/{id}/run starts the harvest lifecycle and returns run id; polling registry for due sources; no Airflow."
1. `POST /sources/{id}/run` starts the harvest lifecycle and returns a run id -> scenarios: run-active-source, run-unknown-source, run-inactive-source
2. Polling registry for due sources -> scenarios: due-sources-never-harvested, due-sources-excludes-recent, due-sources-includes-elapsed, due-sources-excludes-inactive
3. No Airflow -> verified by inspection: no Airflow package, image, or reference added anywhere in this change

## Affected
Capabilities: `spec/capabilities/dispatcher.md` (new)   Docs/contracts: `migrations/0003_dispatcher_runs.{up,down}.sql` (new table — not in the Confluence Contracts' Postgres schema v0, which only lists the five original tables; flagged as a provisional addition, see Risks below), `docker-compose.yml` (scheduler build context), `scheduler/Dockerfile`, `scheduler/requirements.txt` (adds `psycopg[binary]`, `croniter`).

## Risks and open questions
- `dispatcher_runs` is a new table not listed in the Confluence Contracts "Postgres schema v0". Since it is explicitly provisional (superseded by `harvest_runs` in the harvest-core epic), it is not proposed as a permanent schema addition; the Confluence page is not updated for it to avoid documenting a table expected to be replaced within 1-2 stories. If the harvest-core epic lands differently than expected, this choice should be revisited then.
- `GET /sources/due`'s cron-due computation uses the new `croniter` dependency (pure Python, no cloud SDK) rather than hand-rolling cron math, to stay correct for the full 5-field cron grammar already validated by `POST /sources`.
- No compose cron loop is wired up in this story; `GET /sources/due` is proven correct in isolation but not yet exercised end-to-end by an actual scheduler loop.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR.
