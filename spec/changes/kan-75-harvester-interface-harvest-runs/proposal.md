# KAN-75: Extend harvester interface and add harvest_runs table

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-75   Epic: 10 Harvester framework - planning, scoping, validation   Branch: kepler/kan-75-extend-harvester-interface-add

## Why
`docs/HARVESTERS.md` and `spec/capabilities/harvester-framework.md` already describe the full harvester lifecycle (connect/discover/profile/plan/harvest/normalize/validate) and the `harvest_runs` state machine, but neither exists in code yet: there is no `harvesters/` package, and the only run-tracking table is the deliberately provisional `dispatcher_runs` (added in KAN-106, which explicitly defers the full lifecycle table to this epic). This story delivers the shared interface and the `harvest_runs` table so later stories (concrete Git/SQL/upload harvesters) have a contract and a place to record run state, instead of each inventing its own.

## What changes
- Add a `harvesters` package with an abstract `Harvester` base class exposing `connect`, `discover`, `profile`, `plan`, `harvest`, `normalize`, `validate`, matching the interface in `docs/HARVESTERS.md` section 2.
- Add the supporting value types used in that interface's signatures (`ConnectionResult`, `ScopeTree`, `Profile`, `HarvestPlan`, `RawObject`, `Entity`, `Edge`, `Chunk`, `ValidationReport`) as plain dataclasses, cloud-neutral, no I/O.
- Add a `HarvestRunState` enum with the eleven states from `docs/HARVESTERS.md` (`CONNECTING, DISCOVERING, PROFILING, PLANNED, APPROVED, HARVESTING, VALIDATING, PUBLISHED, QUARANTINED, FAILED, PARTIAL`).
- Add migration `0004_harvest_runs` creating `harvest_runs(id, source_id, state, plan jsonb, manifest jsonb, error, started_at, updated_at)` with a `CHECK` constraint restricting `state` to the eleven values above.

## In scope
- The `Harvester` ABC and its supporting dataclasses (structural contract only; no concrete harvester implementation for any source type).
- The `harvest_runs` migration (up/down) and its contract test (table/columns exist, valid states accepted, invalid state rejected).
- Unit tests proving the ABC cannot be instantiated without all seven methods and that a minimal concrete subclass satisfies it.

## Out of scope
- Any concrete harvester (Git, SQL database, SharePoint, Tableau, upload) — later stories in epics 3/7 per `CLAUDE.md` "Build order".
- Wiring `harvest_runs` into the scheduler/dispatcher or emitting `harvest.completed` events — that is the later harvest-core stories (`docs/MILESTONES.md` "B4 Harvest core | 75, 12, 76, 77, 85"), not named in this story's AC.
- Migrating or deprecating `dispatcher_runs` — KAN-106 flagged it as provisional and expected to be superseded once this epic lands, but no story has asked for that migration yet; changing or dropping it here would be a scope change outside KAN-75's AC.
- Budgets, the validator's specific checks (completeness, exclusion integrity, etc.) and the plan-approval UI — covered by other `harvester-framework` requirements already in the capability spec (Budgets, Discover before download, Metadata first) but not part of this story's AC, which only asks for the interface shape and the run table.

## Acceptance criteria (from Jira)
"AC: connect, discover, profile, plan, harvest, normalize, validate in the interface; harvest_runs with states CONNECTING to PUBLISHED/QUARANTINED/FAILED; migration included."
1. `connect, discover, profile, plan, harvest, normalize, validate` in the interface -> scenarios: harvester-interface-has-all-stages, abstract-class-cannot-skip-a-method
2. `harvest_runs` with states CONNECTING to PUBLISHED/QUARANTINED/FAILED -> scenarios: harvest-runs-table-created, harvest-runs-accepts-valid-states, harvest-runs-rejects-invalid-state
3. Migration included -> scenarios: migration-up-creates-table, migration-down-drops-table, migration-reapply-is-no-op

## Affected
Capabilities: `spec/capabilities/harvester-framework.md` (Lifecycle requirement, now implemented)   Docs/contracts: `migrations/0004_harvest_runs.{up,down}.sql` (new table, now matches the Confluence Contracts intent referenced in `CLAUDE.md`), no Confluence edit needed since the harvester interface contract there is unchanged in shape — only now backed by code.

## Risks and open questions
- `dispatcher_runs` and `harvest_runs` now both exist and overlap in purpose. Left as-is per "Out of scope" above; reconciling them (or migrating the dispatcher to write into `harvest_runs`) should be its own story once a concrete harvester needs to drive the full state machine.
- The `plan`/`manifest` columns on `harvest_runs` are typed `jsonb` with no fixed shape yet, since `HarvestPlan`/manifest formats are not finalized until a concrete harvester story defines them; this is consistent with `sources.config_json` being untyped jsonb too.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR.
