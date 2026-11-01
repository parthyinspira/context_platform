# Verification (lite)

Status: PASS
Date: 2026-10-31   Commit: pre-commit (branch m8-ui-wizard-and-runs)

| Acceptance criterion | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Shows what will be pulled and skipped by type and size | `ui/test/AddSourceWizard.plan.test.jsx::shows pulled/skipped groups, estimates and no warnings when none apply` | PASS |
| Estimates for bytes/files/time/tokens | same test (asserts estimate-bytes/estimate-tokens) | PASS |
| Budget warnings | `::shows a budget warning when the plan response includes one` | PASS |
| Editable rules | `::sends edited include/exclude patterns when starting the run` | PASS |
| Run now | `::navigates to the run view on successful Run now`, `::shows an error and stays on the step when Run now fails` | PASS |

Supporting: `npm test` (ui/) → 78 passed (5 new).

Not verified: real byte-level "pulled vs. skipped" split (see plan.md Risks — the backend's generic `Profile` shape has no such field; `counts_by_type` + include/exclude patterns stand in for it); real browser rendering (Vitest + jsdom only, per lite mode).
