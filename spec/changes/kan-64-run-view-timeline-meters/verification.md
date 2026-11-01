# Verification (lite)

Status: PASS
Date: 2026-10-31   Commit: pre-commit (branch m8-ui-wizard-and-runs)

| Acceptance criterion | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Live stage and counts | `ui/test/RunView.test.jsx::shows the live stage as active with manifest counts`, `::marks the run done once it reaches a terminal state and stops polling` | PASS |
| Log stream | `::renders one log line per manifest entry in order` | PASS |
| Meters for files/bytes/time/tokens | `::shows a files meter with value/max and an empty tokens meter when unset` | PASS |
| Stop button | `::shows Stop while non-terminal and hides it once the run is terminal`, `::calling Stop shows the resulting failed state` | PASS |
| Final state with next steps | `::shows a report link when published and a back-to-sources link when failed` | PASS |

Backend support (small, additive extension to KAN-58's `GET /runs/{id}`): `api/tests/test_runs.py::test_get_run_sums_fetched_bytes_and_lists_log_entries` — PASS.

Supporting: `npm test` (ui/) → 84 passed (RunView.test.jsx fully rewritten: 7 tests). `python -m pytest api/tests -q` → 43 passed.

Not verified: real-time polling cadence against a live backend (Vitest mocks `getRun`/`stopRun`, per lite mode — no Docker run per story); bytes/time/tokens Meters show 0 against budget rather than a real live value (see plan.md Risks — no live tracking exists upstream yet); a real `docker compose` end-to-end run reaching PUBLISHED is still blocked on git harvester `normalize()`/`validate()` (pre-existing, KAN-58's risk).
