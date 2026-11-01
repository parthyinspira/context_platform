# Verification (lite)

Status: PASS
Date: 2026-10-31   Commit: pre-commit (branch m8-ui-wizard-and-runs)

| Acceptance criterion | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Shows repos/databases/sites as a tree with sizes and counts | `ui/test/AddSourceWizard.discover.test.jsx::renders the discovered tree with sizes and counts nested under parents` | PASS |
| Checkbox selection | `::toggling a parent checkbox checks all of its children` | PASS |
| Search | `::filters the tree to matches and their ancestors when searching` | PASS |
| Select recommended | `::select recommended checks every leaf node` | PASS |

Also updated `ui/test/AddSourceWizard.test.jsx` and `ui/test/SourcesScreen.test.jsx` to reflect that the wizard now advances into the discover step (and stays open) after a source is created, instead of closing immediately (KAN-61's interim behavior).

Supporting: `npm test` (ui/) → 73 passed (4 new discover-step tests).

Not verified: "recommended" has no real scoring signal upstream (documented in plan.md as select-all-leaves); real browser rendering (Vitest + jsdom only, per lite mode).
