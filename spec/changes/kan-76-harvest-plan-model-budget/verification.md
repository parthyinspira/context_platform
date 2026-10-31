# Verification

Status: PASS
Date: 2026-10-31   Commit: f4ec937

## Checks
| Check | Result |
|---|---|
| Lint (`ruff check harvesters --config pyproject.toml`) | PASS, no findings |
| Tests (`python -m pytest harvesters/tests -q`) | PASS, 11 passed |
| docker compose up exercised | Not applicable — pure in-memory module, no service, no compose change |
| contract-check | No mismatches: no schema/ontology/harvester-interface/adapter/MCP change; no secrets in diff |
| Definition of Done | Tests first, within proposal scope, docs/spec delta added, CI wired |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Harvest plan model / include-exclude-precedence | `harvesters/tests/test_plan.py::test_include_exclude_denylist_wins_over_allowlist` | PASS |
| Harvest plan model / plan-holds-caps-and-budgets | `harvesters/tests/test_plan.py::test_plan_holds_caps_and_budgets` | PASS |
| Harvest plan model / default-plan-is-unrestricted | `harvesters/tests/test_plan.py::test_default_plan_has_no_caps_or_budgets`, `test_no_include_patterns_means_everything_not_excluded_is_included` | PASS |
| Budgets / budget hit (files) | `harvesters/tests/test_budget.py::test_file_budget_hit_stops_cleanly_and_marks_partial` | PASS |
| Budgets / budget hit (bytes) | `harvesters/tests/test_budget.py::test_byte_budget_hit_stops_cleanly_and_marks_partial` | PASS |
| Budgets / budget hit (tokens) | `harvesters/tests/test_budget.py::test_token_budget_hit_stops_cleanly_and_marks_partial` | PASS |
| Budgets / budget hit (time) | `harvesters/tests/test_budget.py::test_time_budget_hit_stops_cleanly_and_marks_partial` | PASS |
| Budgets / report names the exceeded budget | `harvesters/tests/test_budget.py::test_report_names_the_exceeded_budget` | PASS |
| Budgets / run completes when no budget is hit | `harvesters/tests/test_budget.py::test_run_completes_when_no_budget_is_hit` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| 1. Plan holds include/exclude rules, caps and budgets (files, bytes, time, tokens) | plan-holds-caps-and-budgets, include-exclude-precedence, default-plan-is-unrestricted | PASS |
| 2. Run stops cleanly and is marked PARTIAL when a budget is hit | budget hit (files/bytes/tokens/time), report names the exceeded budget, run completes when no budget is hit | PASS |

## Not verified
- End-to-end use by a real harvester: no harvester (Git or otherwise) exists yet in this repo (Epic 3 not built), so this module has no production call site to exercise beyond its own unit tests — by design, per the proposal's "Out of scope" section, matching the precedent set by `spec/archive/kan-82-secret-pii-scanner-redaction`.
- Persistence of `RunStatus` (`PARTIAL`/`COMPLETED`) to a `harvest_runs` table: that table doesn't exist yet (Epic 4 scope); `RunStatus` here is returned to the caller in memory only.
- Full-repo `python -m pytest` (all packages at once) was not run: the repo's root conftest setup causes a pre-existing module-name collision between `api/tests/test_health.py` and `scheduler/tests/test_health.py` unrelated to this change (CI runs tests per-package via a matrix, which is what was used here: `python -m pytest harvesters/tests -q`).
