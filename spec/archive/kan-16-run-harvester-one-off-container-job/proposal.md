# KAN-16: Run harvester as a one-off container job

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-16   Epic: 10 Harvester framework - planning, scoping, validation   Branch: kepler/kan-16-run-harvester-one-off

## Why
`spec/capabilities/dispatcher.md` already notes "no harvester container exists yet; `POST /sources/{id}/run` ... publishes the event a future harvester will consume, but does not itself launch a harvester." `spec/capabilities/harvester-framework.md` requires every run to record its state in `harvest_runs`, and `harvest_validation/gate.py` (KAN-85) already contains the pure publish/quarantine decision a run needs, waiting for "whichever story wires the validator into a concrete `Harvester.validate()` override" (per its docstring) and an orchestrator to call it. All the pieces (`Harvester` base/registry KAN-75/12, `HarvestPlan` KAN-76, `Manifest` KAN-77, `PublishQuarantineGate` KAN-85, `EventBus`/`ObjectStore`/`SecretStore` adapters) exist; nothing drives them end to end as a container process yet. This story adds that driver.

## What changes
- New `harvesters/run.py`: a one-off runner/CLI entrypoint that, given a `source_id` and `plan_id`:
  1. loads the `harvest_runs` row by `plan_id` (verifying it belongs to `source_id`) and the `sources` row by `source_id`, via a plain `psycopg` connection factory built from `DATABASE_URL` (same pattern as `scheduler/app/db.py` and `adapters/event_bus/postgres_outbox.py`);
  2. looks up the registered `Harvester` for the source's `type` via `harvesters.registry.get_harvester`;
  3. decodes the run's stored `plan` JSONB into a `harvesters.framework.plan.HarvestPlan`;
  4. drives `connect -> discover -> harvest -> normalize` using the existing `Harvester` lifecycle methods, recording every discovered/fetched/failed object in a `harvesters.framework.manifest.Manifest`;
  5. calls `Harvester.validate(plan, manifest_entries)` for a `ValidationReport`, then `harvest_validation.gate.PublishQuarantineGate.evaluate(...)` to decide `PUBLISHED` vs `QUARANTINED`;
  6. writes each state transition (`HARVESTING`, `VALIDATING`, final state, or `FAILED` on any exception) plus the manifest and any error back to `harvest_runs` via plain `UPDATE` statements;
  7. publishes `harvest.completed` on the configured `EventBus` (`adapters.factory.get_event_bus`) with the run id, source id, final state, `published`/`warning` flags and record counts.
- The entrypoint reads `SOURCE_ID`, `PLAN_ID`, `DATABASE_URL` from the environment by default (overridable with `--source-id`/`--plan-id` CLI flags for local/compose runs), because Cloud Run Jobs and Container Apps Jobs pass per-task configuration as environment variables, not positional container-command arguments — this is what makes one image runnable the same way under `docker compose run`, a Cloud Run Job and a Container Apps Job.
- `harvesters/Dockerfile`: packages `harvesters/`, `harvest_validation/`, `adapters/`, `ontology/` into an image whose `ENTRYPOINT` is `python -m harvesters.run`, following the existing `scripts/Dockerfile`/`scheduler/Dockerfile` pattern (no platform SDK imports; env-var configuration only).
- `docker-compose.yml`: adds a `harvester` service definition (`profiles: ["harvester"]`, no `ports`, same `DATABASE_URL` default as `api`/`scheduler`) so `docker compose run --rm harvester` is the local equivalent of a Cloud Run Job / Container Apps Job execution; it is not part of the default `docker compose up` set because it is a one-off job, not a long-running service.
- `docs/HARVESTERS.md`: adds a short "Running a harvest" section documenting the `SOURCE_ID`/`PLAN_ID`/`DATABASE_URL` contract and the three run targets (compose, Cloud Run Jobs, Container Apps Jobs), so this becomes the documented interface other stories build a dispatcher-to-job launcher against.

### Design decision: what "plan id" means
No `plans` table exists in the Postgres schema v0 (`CLAUDE.md`) or any migration. The only place a `HarvestPlan` is persisted is the `plan JSONB` column on the `harvest_runs` row itself (migration `0004_harvest_runs.up.sql`), once that row has reached `PLANNED`/`APPROVED`. This story therefore treats the KAN-16 "plan id" as `harvest_runs.id`: the runner loads the plan from that row's `plan` column rather than from a separate table. This keeps the contract consistent with the schema that exists today; if a future story introduces a standalone `plans` table, the runner's `HarvestRunStore.load` is the one place that would change. Flagged under Risks below.

### Design decision: what "the lifecycle end to end" covers here
Per `CLAUDE.md`'s flow ("harvester (discover/fetch/normalize) -> `harvest.completed` -> normalizer writes entities, edges, chunks, embeddings -> ontology updater..."), persisting `Entity`/`Edge`/`Chunk` records to Postgres is explicitly the job of a separate downstream **normalizer** consumer of `harvest.completed`, not the harvester container itself — no `EntityWriter`/`EdgeWriter` adapter exists yet (only `adapters.chunks.PostgresChunkWriter`, which requires a already-persisted `entity_id` foreign key that doesn't exist until a normalizer runs). This story's runner therefore calls `normalize()` to produce in-memory records (for the manifest, the validator's ontology-conformance input, and the published event's counts) but does not write them to `entities`/`edges`/`chunks` — that persistence is explicitly out of scope, left to the future normalizer story the architecture doc already describes.

## In scope
- `harvesters/run.py`: the runner driving connect/discover/harvest/normalize/validate/gate and `harvest_runs` state writes, reusing existing lifecycle types, the registry, the manifest, the gate and the `EventBus`/`SecretStore` adapters — no new abstractions duplicating any of these.
- `harvesters/Dockerfile` and the `docker-compose.yml` `harvester` service, so the same image is exercised locally.
- Unit tests for the runner against a fake Postgres connection and a fake `EventBus` (no live Postgres required, matching the existing adapter test pattern), covering: success (`PUBLISHED`), quarantine (`QUARANTINED` on a `FAIL` validation), connect failure (`FAILED`, no event marked published), unknown `plan_id`/mismatched `source_id` (clear error, no partial state writes), and that `source_id`/`plan_id` are read from the environment when CLI flags are omitted.
- `docs/HARVESTERS.md` documentation of the run contract.
- Spec delta on `spec/capabilities/harvester-framework.md` adding a "Harvester runs as a one-off container" requirement.

## Out of scope
- Any `plans` table/migration — none exists; see the design decision above.
- Persisting `Entity`/`Edge`/`Chunk` records to Postgres (the normalizer) — a separate, future story per the architecture flow in `CLAUDE.md`.
- Actually deploying/configuring a GCP Cloud Run Job or Azure Container Apps Job resource (Terraform/IaC, scheduling) — this story only makes the container image itself portable to those targets (env-var configuration, no platform SDK calls, clean exit codes); provisioning those cloud resources is a later infra story.
- Wiring the dispatcher's `harvest.requested` event (KAN-7/106) to actually launch this container — the dispatcher capability already documents that no launcher exists yet; connecting `harvest.requested` to "run this job with this source_id/plan_id" is separate orchestration left for a future story, since it requires choosing a job-launch mechanism per platform (compose `run`, Cloud Run Jobs API, Container Apps Jobs API) which is exactly the portability problem the adapters pattern is meant to isolate.
- Creating the `harvest_runs` row (`CONNECTING` -> ... -> `PLANNED` -> `APPROVED`) in the first place — that belongs to the planning stages (KAN-75/76 already cover `plan()`/`HarvestPlan`); this story only consumes an already-`PLANNED`/`APPROVED` row.

## Acceptance criteria (from Jira)
"harvester image takes source_id and plan id, runs the lifecycle end to end, writes harvest_runs state, publishes harvest.completed; the same image works under compose, Cloud Run Jobs and Container Apps Jobs."
1. Harvester image takes `source_id` and `plan id` -> scenario: `runner-reads-source-id-and-plan-id-from-env-or-cli`
2. Runs the lifecycle end to end -> scenarios: `runner-drives-full-lifecycle-to-published`, `runner-quarantines-on-failed-validation`, `runner-fails-cleanly-on-connect-error`
3. Writes `harvest_runs` state -> scenarios: same three above, each asserting the state transitions written; plus `runner-rejects-unknown-plan-id`
4. Publishes `harvest.completed` -> scenarios: `runner-drives-full-lifecycle-to-published`, `runner-quarantines-on-failed-validation`
5. The same image works under compose, Cloud Run Jobs and Container Apps Jobs -> scenario: `runner-is-platform-portable` (env-var-only configuration, no cloud SDK imports, `harvesters/Dockerfile` has no platform-specific base or entrypoint assumptions) plus the `docker-compose.yml` `harvester` service as the compose instance of the same image; actually running under a live Cloud Run Job or Container Apps Job is infrastructure this hackathon environment cannot provision, so that half of the scenario is **not verified end-to-end** (see Risks).

## Affected
Capabilities: `spec/capabilities/harvester-framework.md` (modified — adds the "one-off container" requirement). Docs: `docs/HARVESTERS.md` (modified — documents the run contract). Code: new `harvesters/run.py`, `harvesters/tests/test_run.py`, `harvesters/Dockerfile`; modified `docker-compose.yml`.
Contracts: no schema/ontology/harvester-interface change (the `Harvester` ABC itself is untouched); the Confluence Contracts page does not need an update for this story, since it documents the `Harvester` class contract and schema, not the container packaging around it.

## Risks and open questions
- "Plan id" is interpreted as `harvest_runs.id` (see design decision above) because no `plans` table exists; if a future story adds one, this mapping will need to change.
- Entity/Edge/Chunk persistence (the normalizer) is out of scope; the `harvest.completed` event carries record counts from `normalize()` output but no downstream consumer writes them yet, matching the current state of the rest of the repo.
- Actually running this image as a live Cloud Run Job or Azure Container Apps Job cannot be verified in this hackathon/dev environment; verification instead checks the image/entrypoint are platform-neutral (env-var config, no cloud SDK imports in `harvesters/`, a clean `CMD`/`ENTRYPOINT`), and that `docker compose run harvester` and a plain `python -m harvesters.run` both work the same way locally.
- No harvester type is registered for any real source today outside test fixtures (git/document harvesters are separate stories); the runner is exercised in tests against the registry's fixture harvesters, the same pattern `harvesters/tests/test_registry.py` already uses.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR.
