# Verification

Status: PASS
Date: 2026-10-31   Commit: 1fe4422 (merge of origin/main into this branch)

## Checks
| Check | Result |
|---|---|
| Lint | PASS - `python -m ruff check harvesters/` clean |
| Tests (full suite) | PASS - `harvesters` 18/18, `scripts/tests/test_migrate.py` 7/7 (live Postgres via Docker), `adapters` 36/36, `ontology` 12/12, `api` 28/28, `scheduler` 8/8, `harvest_validation` 13/13. `ui` not touched/run (no UI change in this story) |
| docker compose up exercised | NOT RUN - this story extends an existing library package and adds a migration, no new service/container; migration tests used a disposable `pgvector/pgvector:pg16` container directly (see `scripts/tests/conftest.py`), proving the SQL against the real engine without needing the full compose stack |
| contract-check | PASS, with one pre-existing gap flagged below (harvest_runs not yet in Confluence Contracts) |
| secret-scan | PASS - no secret-shaped values in the diff; `.env` untracked, only `.env.example` |
| Definition of Done | PASS for this story's scope (interface + table); see "Not verified" for what a later story must still prove |

## Reconciliation with concurrently-merged stories
While this story was being developed, **KAN-12** (`harvesters/base.py`, `harvesters/registry.py`) and **KAN-76** (`harvesters/framework/` with `HarvestPlan`/`Budgets`) merged to `main`. The first draft of this change wrote a standalone, competing `harvesters/interface.py`. Per a human decision made during PR review, it was reworked to:
- Extend `harvesters/base.py`'s existing `Harvester` ABC in place (its own docstring already anticipated this exact extension) rather than add a second class.
- Reuse `harvesters.framework.HarvestPlan`/`Budgets` for `plan()` instead of a new duplicate plan type.
- Update `harvesters/tests/{test_base,test_registry,fixtures}.py` (all from KAN-12) to the extended seven-method contract.
- Update `spec/capabilities/harvester-framework.md`'s "Base class and plugin registry" requirement to describe the extended interface.

`git diff origin/main...HEAD` touches only `harvesters/base.py`, `harvesters/tests/*`, the two migration files, `scripts/tests/test_migrate.py`, and this change folder — no deletions of KAN-12/KAN-76 code, and the merge with `origin/main` completed with no unresolved conflicts.

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Lifecycle / full run | Not independently re-proven here; this scenario describes end-to-end run-state progression, which requires a concrete harvester (out of scope, see proposal.md). The interface and table it depends on are proven below. | Deferred to concrete-harvester story |
| Lifecycle / harvester-interface-has-all-stages | `harvesters/tests/test_base.py::test_base_class_contract_full_implementation` (asserts `connect`, `discover`, `profile`, `plan`, `harvest`, `normalize`, `validate` all callable and typed as documented) | PASS |
| Lifecycle / abstract-class-cannot-skip-a-method | `harvesters/tests/test_base.py::test_cannot_instantiate_base_class_directly`, `::test_cannot_instantiate_incomplete_subclass` | PASS |
| Lifecycle / harvest-runs-table-created | `scripts/tests/test_migrate.py::test_harvest_runs_table_has_contract_columns` | PASS |
| Lifecycle / harvest-runs-accepts-valid-states | `scripts/tests/test_migrate.py::test_harvest_runs_accepts_every_lifecycle_state` | PASS |
| Lifecycle / harvest-runs-rejects-invalid-state | `scripts/tests/test_migrate.py::test_harvest_runs_rejects_unknown_state` | PASS |
| Lifecycle / migration-up-creates-table | `scripts/tests/test_migrate.py::test_fresh_database_creates_all_core_tables_with_contract_columns` (existing, unaffected) + `test_harvest_runs_table_has_contract_columns` | PASS |
| Lifecycle / migration-down-drops-table | `scripts/tests/test_migrate.py::test_harvest_runs_dropped_on_rollback` | PASS |
| Lifecycle / migration-reapply-is-no-op | `scripts/tests/test_migrate.py::test_reapplying_migrations_is_a_no_op` (existing, unaffected, now also covers version `0004`) | PASS |
| Base class and plugin registry / base-class-contract | `harvesters/tests/test_base.py::test_base_class_contract_full_implementation`, `harvesters/tests/test_registry.py` (registry still resolves `FixtureHarvester` subclasses implementing all seven methods) | PASS |
| Base class and plugin registry / cannot-instantiate-incomplete-subclass | `harvesters/tests/test_base.py::test_cannot_instantiate_incomplete_subclass` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| `connect, discover, profile, plan, harvest, normalize, validate` in the interface | harvester-interface-has-all-stages, abstract-class-cannot-skip-a-method | PASS - implemented on the existing `harvesters.base.Harvester` ABC (extended, not duplicated) |
| `harvest_runs` with states CONNECTING to PUBLISHED/QUARANTINED/FAILED | harvest-runs-table-created, harvest-runs-accepts-valid-states, harvest-runs-rejects-invalid-state | PASS (implemented with the full 11-state set from `docs/HARVESTERS.md`, a superset including CONNECTING, PUBLISHED, QUARANTINED and FAILED named in the AC) |
| Migration included | migration-up-creates-table, migration-down-drops-table, migration-reapply-is-no-op | PASS |

## Not verified
- End-to-end state progression through a real run (`Lifecycle / full run` scenario) — needs a concrete harvester to drive `connect` -> ... -> `validate` and write rows to `harvest_runs`; no concrete harvester exists yet (out of scope for this story, see proposal.md "Out of scope").
- `harvest_runs` is not yet wired into the scheduler/dispatcher or any event (`harvest.completed`); it is a standalone table and Python contract only, as scoped.
- The overlap between the new `harvest_runs` and the existing provisional `dispatcher_runs` (added in KAN-106) is not reconciled; flagged as a risk in `proposal.md`.
- `harvest_runs` is not yet listed in the Confluence Contracts "Postgres schema v0" page, and `CLAUDE.md`'s own schema list is also not updated with `harvest_runs`; left unedited for the same reason `dispatcher_runs` was left out (provisional-feeling addition during an epic still in progress) — flagging for human judgment at PR rather than editing CLAUDE.md/Confluence unilaterally.
- `docker compose up` was not exercised since no service or container changed; migration correctness was proven directly against a live Postgres container instead.
- No concrete harvester subclass exists yet to exercise `harvest()`'s budget/plan-filtering behavior against a real source; only the fixture harvester in `harvesters/tests/fixtures.py` exercises it.
