# Verification (lite)

Status: PASS
Date: 2026-10-31   Commit: pre-commit (branch m8-ui-wizard-and-runs)

| Acceptance criterion | Evidence (test, command, screenshot) | Result |
|---|---|---|
| PASS/WARN/FAIL badge | `ui/test/ValidationReportScreen.test.jsx::shows the overall status badge for the report` | PASS |
| Every check with counts and samples | `::lists every check with its counts and samples, showing 'none' when empty` | PASS |
| Quarantine explanation | `::shows the quarantine explanation only when the run is quarantined`, `::does not show the quarantine explanation for a published run` | PASS |

Also: 404 fallback (`::shows a fallback with the run's state and error when no report exists yet`) and end-to-end navigation from `RunView` (`ui/test/App.navigation.test.jsx::navigates from a published run to its validation report and back`).

Supporting: `npm test` (ui/) → 90 passed (5 new ValidationReportScreen tests + 1 new App navigation test).

Not verified: a live end-to-end report from a real harvest run (see KAN-58's plan.md Risks — no harvester populates `harvest_runs.report` with real counts/samples yet); real browser rendering (Vitest + jsdom only, per lite mode).
