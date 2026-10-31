# KAN-60: Sources screen with Run button

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-60   Epic: 9 UI and knowledge graph   Branch: kepler/kan-60-sources-screen-run-button

## Why
`docs/HACKATHON_SCOPE.md` names a Sources screen ("List sources with status, last run, validation result; Run button per source") as part of the demo. The `ui` app currently only renders an empty shell (`App.jsx`). The source registry (`GET /sources`) and dispatcher (`POST /sources/{id}/run`) APIs already exist (KAN-8, KAN-106); nothing in the UI calls them yet.

## What changes
- Add client-side navigation to the app shell: `NavRail` items become clickable and switch the active screen (`sources` is reachable; `Graph`/`Runs`/`Agents`/`Settings` stay placeholders since those screens are out of scope here). No router library is added — a small view-state switch in `App.jsx` is enough for this story's AC ("navigates to run view").
- Add a `SourcesScreen` that calls `GET /sources` and renders a table: name (`uri`), type, status, last run, validation badge, and a **Run** action per active source.
- Add a `RunView` that is navigated to after a successful Run call, showing the run id, source id and status returned by `POST /sources/{id}/run`.
- Add a small `api.js` client module reading `VITE_API_BASE_URL` / `VITE_SCHEDULER_BASE_URL` (defaulting to `http://localhost:8000` / `http://localhost:8001`, matching the `API_PORT`/`SCHEDULER_PORT` the compose stack publishes) for the two calls above.
- Empty state: when `GET /sources` returns zero rows, the Sources screen shows an empty-state message instead of a table (no add-source wizard yet — that is a separate, later story per `docs/UI_DESIGN.md` 4.3).

## In scope
- `SourcesScreen`, `RunView`, nav-rail click handling, `api.js`, and tests for all of the above (loading, empty, success, error states; Run success navigates to the run view; Run failure stays on the Sources screen and shows an error).

## Out of scope
- The add-source wizard (`docs/UI_DESIGN.md` 4.3) and the full Run view stage timeline/log stream (`docs/UI_DESIGN.md` 4.4) — those are separate, later stories.
- **Persisted "last run" and "validation badge" data.** No API in this repo yet exposes run history per source or any validation result (`spec/capabilities/dispatcher.md`'s `dispatcher_runs` has no `GET` route; `spec/capabilities/harvest-validation.md`'s validator output is not wired to any endpoint). Adding either is a backend change outside this UI story's scope. The Sources screen therefore shows:
  - **Last run**: "Never" for a source with no run triggered in this browser session, otherwise the status of the last run this session triggered via the Run button (client-side only; not persisted, lost on reload). This satisfies the AC's "last run" column with real, honestly-scoped data rather than inventing a backend read endpoint mid-story.
  - **Validation badge**: a static "Not yet validated" badge for every source, since no validation data exists anywhere in the system yet. Flagged under "Not verified" in `verification.md`.
- A real "Runs" nav screen, compose networking changes, or a reverse proxy in front of `api`/`scheduler` — the browser calls the host-published `API_PORT`/`SCHEDULER_PORT` ports directly, consistent with how `docker-compose.yml` already exposes them.
- Graceful-page routing via URL (back/forward, deep links) — a view-state switch is sufficient for the AC.

## Acceptance criteria (from Jira, KAN-60)
"lists sources with status, last run, validation badge; Run calls dispatcher and navigates to run view; empty state."
1. Lists sources with status, last run, validation badge -> scenarios: sources-list-renders, sources-list-empty-state, sources-list-loading, sources-list-error
2. Run calls dispatcher and navigates to run view -> scenarios: run-button-calls-dispatcher-and-navigates, run-button-error-stays-on-sources
3. Empty state -> scenario: sources-list-empty-state

## Affected
Capabilities: `spec/capabilities/ui.md` (new requirement: Sources screen)   Code: `ui/src/App.jsx`, `ui/src/components/NavRail.jsx`, new `ui/src/components/SourcesScreen.jsx`, `ui/src/components/RunView.jsx`, `ui/src/api.js`, tests under `ui/test/`.

## Risks and open questions
- "Last run" and "validation badge" are client-session-only placeholders, not real persisted data (see Out of scope). If this is unacceptable for the demo, a follow-up story should add `GET /sources/{id}/runs` (or similar) and a validation-result read endpoint; flagged for the human reviewer.
- The UI calls `api`/`scheduler` directly on their host-published ports rather than through a shared base path; this matches the current compose topology (no gateway/proxy exists) and avoids a CORS/proxy change outside this story's scope. FastAPI CORS must allow the UI origin — verified by configuring permissive CORS in both services for local/demo use (already open, single-tenant hackathon stack).

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR.
