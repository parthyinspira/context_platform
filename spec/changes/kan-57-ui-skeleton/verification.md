# Verification

Status: PASS
Date: 2026-10-30   Commit: 4f0e3d4 (PR #9, pre-reviewer-fix) / re-verified after reviewer round 1 fixes

## Reviewer round 1
`story-reviewer` returned APPROVE WITH NITS, with one [blocking] finding (Tailwind scaffolded but unused, contradicting the "styled with Tailwind CSS driven by tokens.json" requirement text) and two nits (duplicated light-theme CSS fallback, Dockerfile healthcheck hardcoding port 3000). All three fixed: `tailwind.config.js` now derives `theme.extend.colors`/`fontFamily`/`borderRadius` from `ui/src/tokens.json`; `App.jsx`/`NavRail.jsx`/`TopBar.jsx` use Tailwind utility classes against those tokens; the redundant hand-written CSS block was removed; the Dockerfile `HEALTHCHECK` now reads `$PORT`. Re-ran `npm test` (23/23 pass), `npm run build` (no longer warns "no utility classes detected"), and `docker build`/`docker run` (`/health` → `{"status":"ok"}`) after the fix.

## Checks
| Check | Result |
|---|---|
| Lint | N/A for this change (no Python files touched; no JS lint configured for `ui/`) |
| Tests (full suite) | PASS — `npm test` in `ui/` (vitest): 23/23 tests passed (tokens.test.js, health.test.js, AppShell.test.jsx) |
| docker compose up exercised | PASS — `docker compose up -d` built all services; `ui` service built and ran via `docker compose up -d ui` (UI_PORT=3910 to avoid a local port clash), reported `healthy`, `/health` returned `{"status":"ok"}`, `/` served the built `index.html` referencing the Vite JS/CSS bundle. Stack torn down with `docker compose down -v` afterward. |
| contract-check | PASS — change is scoped to `ui/`; no schema, ontology, harvester, adapter or MCP contract touched; no cloud SDK imports added |
| secret-scan | PASS — no secrets in diff; only `.env.example` tracked, `.env` untracked and removed after local testing |
| Definition of Done | PASS — tests first, change folder complete, CI updated, verification evidence captured |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| tokens-loaded-light-dark | `ui/test/tokens.test.js` (20 assertions: both themes present, all 9 keys typed, values differ) via `npm test` | PASS |
| app-shell-nav-rail-topbar | `ui/test/AppShell.test.jsx` "renders a nav rail with the five sections and a top bar" via `npm test` | PASS |
| theme-toggle-switches-tokens | `ui/test/AppShell.test.jsx` "toggles the document theme between light and dark" via `npm test` | PASS |
| ui-compose-health | `docker build -t cp-ui-test ./ui` then `docker run -p 3901:3000 cp-ui-test` → `curl http://localhost:3901/health` returned `{"status":"ok"}`; repeated via `docker compose up -d ui` (service reported `healthy`, port mapping `0.0.0.0:3910->3000/tcp`) | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| 1. App runs from docker compose | ui-compose-health | PASS — verified live with `docker compose up -d ui` against the full stack (postgres, migrate, api healthy as prerequisites) |
| 2. Nav rail and top bar | app-shell-nav-rail-topbar | PASS — component test asserts both are present with the five nav items (Graph, Sources, Runs, Agents, Settings) |
| 3. Design tokens loaded from `ui/src/tokens.json` | tokens-loaded-light-dark | PASS — `src/theme.js` reads `tokens.json` and applies CSS custom properties; tested directly |
| 4. Light and dark | theme-toggle-switches-tokens | PASS — toggle in the top bar flips `document.documentElement[data-theme]` and the CSS variables between the `light` and `dark` token sets |

## Not verified
- Visual/pixel-level WCAG AA contrast check of the tokens (full UI_DESIGN.md section 2 colour-blind/contrast validation) — out of scope for this skeleton story; flagged in `docs/UI_DESIGN.md` as "to be validated during build" for later screen work.
- CI's `compose-smoke-test` job (which also brings up `api`/`scheduler`) was exercised manually here, not through an actual GitHub Actions run; it will run for real once the PR is opened.
