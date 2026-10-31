# KAN-57: UI skeleton: React, Vite, Tailwind, tokens.json, app shell, Dockerfile

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-57   Epic: 8 (Demo)   Branch: kepler/kan-57-ui-skeleton-react-vite

## Why
The UI container currently only serves a static placeholder page (`ui/server.js`). Every later UI story (Sources, graph, wizard) needs a real React app shell with design tokens wired up and a theme switch, so this story lays that foundation before any screen-specific work starts.

## What changes
- Replace the placeholder server with a Vite + React + Tailwind app, built at image build time and served as static files.
- Add `ui/src/tokens.json` as the single source of design tokens (light and dark), per `docs/UI_DESIGN.md` section 2.
- Add an app shell: left nav rail (Graph, Sources, Runs, Agents, Settings) and a top bar (global search placeholder, environment badge, theme toggle, user).
- Keep `ui/Dockerfile` building and serving the app so `docker compose up` still brings up the `ui` service with a working `/health` endpoint.

## In scope
- App shell (nav rail + top bar), tokens.json, light/dark theme switch, Vite build, Tailwind wired to tokens, Dockerfile update, tests for tokens and app shell.

## Out of scope
- Any real screen content (Sources table, graph canvas, wizard, run view, validation report) — later stories per `docs/HACKATHON_SCOPE.md`.
- Wiring to the context service API.

## Acceptance criteria (from Jira)
1. App runs from `docker compose up` -> scenarios: ui-compose-health
2. Nav rail and top bar -> scenarios: app-shell-nav-rail-topbar
3. Design tokens loaded from `ui/src/tokens.json` -> scenarios: tokens-loaded-light-dark
4. Light and dark -> scenarios: theme-toggle-switches-tokens

## Affected
Capabilities: `spec/capabilities/foundation.md` (UI service, already covered by the existing `ci-test-runs`/`compose-smoke-test` scenarios — no contract change). Docs: `docs/UI_DESIGN.md` (already specifies tokens.json and app shell; no change needed).

## Risks and open questions
- Docker Desktop may not be available in this environment to exercise `docker compose up`; build-only verification (`docker build`, `npm run build`, `vite build`) and container `node --test`/`vitest` runs stand in, noted explicitly in `verification.md` if so.

## Changes during development
- Round 1 reviewer finding ([blocking]): Tailwind was scaffolded but unused (`npm run build` warned "no utility classes detected"); `tailwind.config.js` did not read `ui/src/tokens.json`. Fixed by generating `theme.extend.colors`/`fontFamily`/`borderRadius` from `tokens.json` and switching `App.jsx`, `NavRail.jsx`, `TopBar.jsx` to Tailwind utility classes backed by the CSS custom properties `theme.js` sets; removed the now-redundant hand-written CSS in `index.css`.
- Round 1 reviewer nit: Dockerfile `HEALTHCHECK` hardcoded port 3000 instead of respecting `$PORT`; fixed to read `process.env.PORT`.

## Approval
Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
