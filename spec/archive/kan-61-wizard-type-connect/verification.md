# Verification (lite)

Status: PASS
Date: 2026-10-31   Commit: pre-commit (branch m8-ui-wizard-and-runs)

| Acceptance criterion | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Type tiles | `ui/test/AddSourceWizard.test.jsx::renders six type tiles with only Git enabled` | PASS |
| Credential form per type | `ui/test/AddSourceWizard.test.jsx::advances to the connect step after selecting Git` (Git form); other types stay disabled tiles | PASS |
| Test connection with clear success/error | `::shows success and blanks the credentials field after a successful test`, `::shows an error message when test connection fails`, `::shows a loading indicator while test connection is in flight` | PASS |
| Secrets masked and never shown again | `::shows success and blanks the credentials field after a successful test` (asserts input value is `""` post-success) | PASS |

Also: `ui/test/SourcesScreen.test.jsx::opens the add-source wizard and refreshes the list once a source is created`.

Supporting: `npm test` (ui/) → 69 passed (7 new: 6 AddSourceWizard + 1 SourcesScreen).

Not verified: real browser rendering/visual check (Vitest + jsdom only, per lite mode — no Docker/browser run per story); only the Git credential form exists, other types are disabled tiles by design (see plan.md Risks).
