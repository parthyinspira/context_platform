# Verification

Status: PASS
Date: 2026-10-31   Commit: d3a6344 (pending this change's commit)

## Checks
| Check | Result |
|---|---|
| Lint | PASS - `python -m ruff check .` clean on all changed files (`harvesters/`, `scripts/tests/test_migrate.py`); the one remaining repo-wide finding in `api/tests/test_source_registered_consumer.py` pre-exists on `origin/main`, confirmed via `git stash` |
| Tests (full suite) | PASS - `harvesters` 5/5, `scripts/tests/test_migrate.py` 7/7 (live Postgres via Docker), `adapters` 22/22, `ontology` 12/12, `api` 28/28, `scheduler` 8/8. `ui` not touched/run (no UI change in this story) |
| docker compose up exercised | NOT RUN - this story adds a library package and a migration, no new service/container; migration tests used a disposable `pgvector/pgvector:pg16` container directly (see `scripts/tests/conftest.py`), proving the SQL against the real engine without needing the full compose stack |
| contract-check | PASS - see below |
| Definition of Done | PASS for this story's scope (interface + table); see "Not verified" for what a later story must still prove |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Lifecycle / full run | Not independently re-proven here; this scenario describes end-to-end run-state progression, which requires a concrete harvester (out of scope, see proposal.md). The interface and table it depends on are proven below. | Deferred to concrete-harvester story |
| Lifecycle / harvester-interface-has-all-stages | `harvesters/tests/test_interface.py::test_harvester_declares_all_seven_stages` | PASS |
| Lifecycle / abstract-class-cannot-skip-a-method | `harvesters/tests/test_interface.py::test_harvester_cannot_be_instantiated_directly`, `::test_subclass_missing_a_method_cannot_be_instantiated` | PASS |
| Lifecycle / harvest-runs-table-created | `scripts/tests/test_migrate.py::test_harvest_runs_table_has_contract_columns` | PASS |
| Lifecycle / harvest-runs-accepts-valid-states | `scripts/tests/test_migrate.py::test_harvest_runs_accepts_every_lifecycle_state` | PASS |
| Lifecycle / harvest-runs-rejects-invalid-state | `scripts/tests/test_migrate.py::test_harvest_runs_rejects_unknown_state` | PASS |
| Lifecycle / migration-up-creates-table | `scripts/tests/test_migrate.py::test_fresh_database_creates_all_core_tables_with_contract_columns` (existing, unaffected) + `test_harvest_runs_table_has_contract_columns` | PASS |
| Lifecycle / migration-down-drops-table | `scripts/tests/test_migrate.py::test_harvest_runs_dropped_on_rollback` | PASS |
| Lifecycle / migration-reapply-is-no-op | `scripts/tests/test_migrate.py::test_reapplying_migrations_is_a_no_op` (existing, unaffected, now also covers version `0004`) | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| `connect, discover, profile, plan, harvest, normalize, validate` in the interface | harvester-interface-has-all-stages, abstract-class-cannot-skip-a-method | PASS |
| `harvest_runs` with states CONNECTING to PUBLISHED/QUARANTINED/FAILED | harvest-runs-table-created, harvest-runs-accepts-valid-states, harvest-runs-rejects-invalid-state | PASS (implemented with the full 11-state set from `docs/HARVESTERS.md`, which is a superset including CONNECTING, PUBLISHED, QUARANTINED and FAILED named in the AC) |
| Migration included | migration-up-creates-table, migration-down-drops-table, migration-reapply-is-no-op | PASS |

## Not verified
- End-to-end state progression through a real run (`Lifecycle / full run` scenario) — needs a concrete harvester to drive `connect` -> ... -> `validate` and write rows to `harvest_runs`; no concrete harvester exists yet (out of scope for this story, see proposal.md "Out of scope").
- `harvest_runs` is not yet wired into the scheduler/dispatcher or any event (`harvest.completed`); it is a standalone table and Python contract only, as scoped.
- The overlap between the new `harvest_runs` and the existing provisional `dispatcher_runs` (added in KAN-106) is not reconciled; flagged as a risk in `proposal.md`.
- `harvest_runs` is not yet listed in the Confluence Contracts "Postgres schema v0" page; left unedited for the same reason `dispatcher_runs` was left out (provisional-feeling addition during an epic still in progress) — flagging for human judgment at PR rather than editing Confluence unilaterally.
- `docker compose up` was not exercised since no service or container changed; migration correctness was proven directly against a live Postgres container instead.
