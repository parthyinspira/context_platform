# Verification

Status: PASS

## Checks
- `npm test` (in `ui/`) -> 31 passed (6 files): `test/tokens.test.js`, `test/health.test.js`, `test/RunView.test.jsx`, `test/AppShell.test.jsx`, `test/SourcesScreen.test.jsx`, `test/App.navigation.test.jsx`
- `npm run build` (in `ui/`) -> builds cleanly to `dist/`
- `python -m pytest api/tests -q` -> 28 passed (unchanged behaviour; confirms CORS addition is non-breaking)
- `python -m pytest scheduler/tests -q` -> 8 passed (unchanged behaviour; confirms CORS addition is non-breaking)
- `secret-scan` skill -> no secrets found; `.env` untracked (`git ls-files` shows only `.env.example`); no key/token/password patterns in the diff
- `contract-check` skill -> no mismatches: no schema/table change (no migration needed), no new ontology types, no cloud SDK imports outside `adapters/`, no MCP tool changes; the only capability change is the `ui.md` delta in this change folder, applied to `spec/capabilities/` at archive time
- `python scripts/spec_check.py spec/changes/kan-60-sources-screen-run-button` -> OK (plan)
- `python scripts/spec_check.py spec/changes/kan-60-sources-screen-run-button --stage=verify` -> OK (verify)

## Scenario evidence
- **sources-list-renders** (`specs/ui.md`): `ui/test/SourcesScreen.test.jsx::"renders sources with status, last run and validation badge"` — asserts the row shows `uri`, `type`, `status`, a "Never" last-run cell, a "Not yet validated" badge, and a Run button.
- **sources-list-empty-state** (`specs/ui.md`): `ui/test/SourcesScreen.test.jsx::"shows an empty state when there are no sources"` — `GET /sources` resolves `[]`, empty state (`data-testid="sources-empty"`) renders.
- **sources-list-loading** (`specs/ui.md`): `ui/test/SourcesScreen.test.jsx::"shows a loading state before sources resolve"` — unresolved promise, `data-testid="sources-loading"` renders.
- **sources-list-error** (`specs/ui.md`): `ui/test/SourcesScreen.test.jsx::"shows an error state when listing sources fails"` — `GET /sources` rejects, `data-testid="sources-error"` renders.
- **run-button-calls-dispatcher-and-navigates** (`specs/ui.md`): `ui/test/SourcesScreen.test.jsx::"calls the dispatcher and navigates to the run view on Run"` asserts `runSource` is called with the source id and `onRunStarted` receives the run; `ui/test/App.navigation.test.jsx::"navigates to the Sources screen and then to the run view after Run"` exercises the same path through `App` end-to-end and asserts the run view (`data-testid="run-view"`) renders with the run id.
- **run-button-error-stays-on-sources** (`specs/ui.md`): `ui/test/SourcesScreen.test.jsx::"stays on the sources list and shows an error when Run fails"` — `runSource` rejects, `data-testid="run-error"` renders, `onRunStarted` is not called, the sources table is still present.

## Acceptance criteria
Jira AC (verbatim, KAN-60): "lists sources with status, last run, validation badge; Run calls dispatcher and navigates to run view; empty state."

1. **Lists sources with status, last run, validation badge** — PASS. Evidence: sources-list-renders above. "Last run" and "validation badge" are scoped per `proposal.md` "Out of scope": no backend endpoint in this repo yet exposes persisted run history or validation results, so the screen shows "Never" / the last run triggered in the current browser session, and a static "Not yet validated" badge for every source. See "Not verified" below.
2. **Run calls dispatcher and navigates to run view** — PASS. Evidence: run-button-calls-dispatcher-and-navigates, run-button-error-stays-on-sources above. The run view shown is a minimal id/source id/status display (`RunView.jsx`), not the full stage-timeline/log-stream run view from `docs/UI_DESIGN.md` 4.4, which is out of scope per `proposal.md`.
3. **Empty state** — PASS. Evidence: sources-list-empty-state above.

## Not verified
- **Persisted "last run" and "validation badge" data.** No API exists yet to read run history per source (`dispatcher_runs` has no `GET` route) or validation results (no validator output is wired to any endpoint). The Sources screen's "last run" column reflects only runs triggered in the current browser session (lost on reload) and the validation badge is a static placeholder for every source. Flagged in `proposal.md` "Out of scope" and "Risks"; a follow-up story should add the missing read endpoint(s) if persisted data is required for the demo.
- **Live `docker compose up` end-to-end run in a browser.** Tests use Vitest/jsdom with the `api.js` module mocked (same approach as other test suites in this repo); the UI was not manually clicked through against a running `docker compose up` stack in this session. `npm run build` was used to confirm the production build compiles; CORS headers were added to both services but not exercised against a live browser request.
- **Nav items other than Sources.** `Graph`/`Runs`/`Agents`/`Settings` remain the existing placeholder view, per `proposal.md` "Out of scope" — only `Sources` routes to new content.
