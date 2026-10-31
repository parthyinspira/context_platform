# Verification

Status: PASS
Date: 2026-10-31   Commit: d3a6344e4134035a5cb9511fee7b6802fff6e678 (pre-commit; see PR for final sha)

## Checks
| Check | Result |
|---|---|
| Lint (`python -m ruff check harvest_validation`) | PASS |
| Tests (`python -m pytest harvest_validation -q`) | PASS - 13 passed |
| Other package suites unaffected (`api`, `scheduler`, `adapters`, `ontology`, `document_parsing`) | PASS - 28, 8, 36, 12, 13 passed respectively, run individually matching CI's per-package invocation |
| docker compose up exercised | Not applicable - pure Python logic package, no service/container added |
| contract-check | No mismatches: no schema/migration, ontology, harvester-interface, adapter, or MCP contract touched; no cloud SDK imports added outside `adapters/` |
| secret-scan | No secrets found in diff; `.env` untracked, only `.env.example` tracked |
| Definition of Done | Code + tests + spec delta + CI wiring done; no docs/Confluence contract change needed (no contract changed) |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| failed validation (failed-validation-quarantines) | `harvest_validation/tests/test_gate.py::test_failed_validation_quarantines_and_keeps_previous_knowledge` | PASS |
| warn validation publishes with warning (warn-validation-publishes-with-warning) | `harvest_validation/tests/test_gate.py::test_warn_validation_publishes_with_warning` | PASS |
| pass validation publishes (pass-validation-publishes) | `harvest_validation/tests/test_gate.py::test_pass_validation_publishes_without_warning` | PASS |
| gate rejects non-validating state (gate-rejects-non-validating-state) | `harvest_validation/tests/test_gate.py::test_gate_rejects_non_validating_state[*]` (9 states) and `::test_gate_rejects_non_validating_state_even_on_fail_status` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| FAIL keeps previous knowledge published and marks QUARANTINED | failed-validation-quarantines | PASS - `FakeKnowledgeStore` untouched when `published=False`; `new_state == QUARANTINED` |
| WARN publishes with warning | warn-validation-publishes-with-warning | PASS - `new_state == PUBLISHED`, `published=True`, `warning=True` |
| State transitions tested | pass-validation-publishes, gate-rejects-non-validating-state | PASS - PASS path transitions to PUBLISHED without warning; evaluating from any of the 9 non-VALIDATING states raises `InvalidRunStateError` with no transition |

## Not verified
- No real `harvest_runs` table or harvester exists yet (confirmed against `spec/archive/kan-106-dispatcher-run-endpoint-ui/proposal.md`: that lifecycle table is scoped to this harvest-core epic, stories 75/12/76/77/85). This story therefore verifies the gate's decision logic and state guard in isolation (with a fake in-memory knowledge store standing in for the graph), not an end-to-end run against a persisted `harvest_runs` row or a real `ValidationReport` producer. Wiring the gate to an actual validator and to `harvest_runs` persistence is left to the later stories that introduce those pieces.
- `document_parsing` is missing from the CI matrix (`.github/workflows/ci.yml`) even though it has its own `requirements*.txt` and passes standalone — a pre-existing gap, left as-is since it is unrelated to this story's scope.
