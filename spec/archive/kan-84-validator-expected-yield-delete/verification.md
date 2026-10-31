# Verification

Status: PASS
Date: 2026-10-31   Commit: (pre-PR working tree; see PR for merge commit)

## Checks
| Check | Result |
|---|---|
| Lint | PASS — `ruff check harvest_validation` and `ruff format --check harvest_validation/validator.py harvest_validation/tests/test_validator.py`: clean |
| Tests (full suite) | PASS — `python -m pytest -q --ignore=scheduler`: 201 passed (new: 28 in `harvest_validation/tests/test_validator.py`). `scheduler/tests/test_health.py` excluded: pre-existing module-name collision with `api/tests/test_health.py`, unrelated to this change (confirmed by stashing this change's files and re-running — the collision reproduces on `main` too) |
| docker compose up exercised | Not applicable — pure Python unit-level change, no service/container affected |
| contract-check | PASS — no schema/migration change; entity types used (`Table`, `Module`, `Job`, `Document`) are all existing Ontology v0 types, none added; no cloud SDK imports; no MCP tool touched; secret-scan found no real secrets (test fixtures use obviously fake values) |
| Definition of Done | PASS — tests first (confirmed via task order), scoped to the proposal, spec delta added, `spec_check` clean at both plan and verify stages |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Standard checks / zero-yield-fails | `harvest_validation/tests/test_validator.py::test_zero_yield_fails` | PASS |
| Standard checks / stack-missing-expected-entities-fails | `harvest_validation/tests/test_validator.py::test_stack_missing_expected_entities_fails` | PASS |
| Standard checks / expected-yield-passes | `harvest_validation/tests/test_validator.py::test_expected_yield_passes`, `::test_expected_yield_skips_unknown_stacks` | PASS |
| Delete sanity / delete-spike | `harvest_validation/tests/test_validator.py::test_delete_spike_fails`, `::test_delete_below_threshold_passes`, `::test_delete_exactly_at_threshold_passes`, `::test_delete_sanity_passes_with_nothing_previously_published`, `::test_delete_sanity_custom_threshold` | PASS |
| Standard checks / unredacted-secret-fails | `harvest_validation/tests/test_validator.py::test_unredacted_secret_fails` | PASS |
| Standard checks / redacted-content-passes | `harvest_validation/tests/test_validator.py::test_redacted_content_passes`, `::test_secrets_check_passes_on_empty_input` | PASS |
| Aggregate report shape (`run_checks`) | `::test_run_checks_all_pass_yields_pass_report`, `::test_run_checks_any_fail_yields_fail_report_with_errors`, `::test_run_checks_partial_fail_still_fails_overall` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Stack yields expected entity types (zero yield fails) | zero-yield-fails, stack-missing-expected-entities-fails, expected-yield-passes | PASS |
| Tombstone spike over threshold quarantines | delete-spike (check returns FAIL; `harvest_validation/gate.py::PublishQuarantineGate`, verified separately in KAN-85, turns a FAIL status into QUARANTINED — not re-wired here, see Not verified) | PASS (check logic); see Not verified for end-to-end wiring |
| Unredacted secrets fail | unredacted-secret-fails | PASS |

## Not verified
- End-to-end wiring of `run_checks`'s output into `PublishQuarantineGate` or a real `harvest_runs` state transition: no concrete harvester or `harvest_runs` persistence exists yet (same gap noted in `spec/archive/kan-85-publish-quarantine-gate/proposal.md`). The gate's own FAIL -> QUARANTINED behavior is already unit-tested in `harvest_validation/tests/test_gate.py`; this story only adds the check logic that would feed it.
- The stack-to-expected-entity-type mapping (`STACK_EXPECTED_ENTITY_TYPES`) is a reasonable reading of `docs/HARVESTERS.md` section 4 but is not itself a named contract; flagged for confirmation when a real Git harvester (epic 3) lands and can be checked against real yields.
- `docker compose up` was not exercised — this change has no runtime/container surface.
