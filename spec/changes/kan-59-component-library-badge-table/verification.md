# Verification

Status: PASS

## Checks
- `npx vitest run` (in `ui/`) -> 54 passed across 12 test files (9 new component/primitive test files + the 3 pre-existing files, unchanged, confirming no regression)
- `npx vite build` (in `ui/`) -> builds cleanly, no errors
- `contract-check` skill -> no mismatches: no schema/migration, ontology, harvester-interface, adapter or MCP-tool contract touched; no cloud SDK imports added; `.env` untracked (`git ls-files` shows only `.env.example`)
- `secret-scan` skill -> no secrets found in the diff; no `password=`/`secret=`/`api_key=`/private-key/cloud-key patterns present
- `python scripts/spec_check.py spec/changes/kan-59-component-library-badge-table` -> OK (plan)
- `python scripts/spec_check.py spec/changes/kan-59-component-library-badge-table --stage=verify` -> OK (verify, after this file was added and all tasks ticked)

## Scenario evidence
- **empty-state-renders-message-and-action** / **skeleton-renders-without-content** / **error-banner-renders-message** (`specs/ui.md` shared primitives): `ui/test/EmptyState.test.jsx`, `ui/test/Skeleton.test.jsx`, `ui/test/ErrorBanner.test.jsx` — message/action rendering, placeholder count, and `role="alert"` message respectively.
- **badge-variants / badge-loading / badge-error / badge-empty**: `ui/test/Badge.test.jsx` — all four `variant`s render icon + label in `state="success"`; `loading` renders a `Skeleton`; `error` renders an `ErrorBanner` (`role="alert"`); `empty` renders an `EmptyState` with "No status".
- **table-columns-rows / table-loading / table-error / table-empty**: `ui/test/DataTable.test.jsx` — header per column + one row per data row in `success`; `Skeleton` in `loading`; `ErrorBanner` with the passed message in `error`; `EmptyState` with the passed message in `empty`.
- **stepper-steps / stepper-loading / stepper-error / stepper-empty**: `ui/test/Stepper.test.jsx` — earlier steps marked `complete`, active step marked `current` with `aria-current="step"`, later steps `pending`, in `success`; `Skeleton` in `loading`; `ErrorBanner` in `error`; `EmptyState` ("No steps configured") in `empty`.
- **scope-tree-nodes / scope-tree-loading / scope-tree-error / scope-tree-empty**: `ui/test/ScopeTree.test.jsx` — nested nodes render label, count and checkbox state (plus an `onToggle` callback test) in `success`; `Skeleton` in `loading`; `ErrorBanner` in `error`; `EmptyState` ("Nothing discovered yet") in `empty`.
- **meter-value / meter-loading / meter-error / meter-empty**: `ui/test/Meter.test.jsx` — labelled `role="progressbar"` with `aria-valuenow`/`aria-valuemax` and numeric "value / max" text in `success`; `Skeleton` in `loading`; `ErrorBanner` in `error`; `EmptyState` ("No budget set") in `empty`.
- **timeline-stages / timeline-loading / timeline-error / timeline-empty**: `ui/test/Timeline.test.jsx` — ordered stages with `data-status` in `success`; `Skeleton` in `loading`; `ErrorBanner` in `error`; `EmptyState` ("No run started") in `empty`.

## Acceptance criteria
Jira AC (verbatim, from the attached issue context): "components match UI_DESIGN.md section 5; each has empty, loading, error and success states."

1. **Components match `UI_DESIGN.md` section 5** — PASS. Evidence: the badge-variants, table-columns-rows, stepper-steps, scope-tree-nodes, meter-value and timeline-stages scenarios above each confirm the component's "success" shape matches its section-5 description (status badge with icon+label; data table with columns/rows; stepper with current/complete steps; checkbox scope tree with per-node counts; labelled budget progress bar; Connect-to-Publish stage list). All components consume colour/spacing/radius exclusively through the existing `ui/tailwind.config.js` token mapping of `ui/src/tokens.json` — no new hard-coded colours were introduced (visually confirmed by reading each component's source; no raw hex values appear outside `tokens.json`).
2. **Each has empty, loading, error and success states** — PASS. Evidence: all 24 per-state scenarios above (4 states x 6 primary components), run against the shared `EmptyState`/`Skeleton`/`ErrorBanner` primitives, which are also directly tested on their own.

## Not verified
- **Visual/design review.** Per `UI_DESIGN.md` section 7, this repo cannot produce Figma files; "matches section 5" is verified against the textual component inventory, token usage and rendered DOM structure in jsdom, not a pixel-level visual comparison or a real browser screenshot.
- **Dark-theme-specific visual QA.** Components were not screenshotted in the dark theme; they use the same CSS custom properties already proven to switch themes by `ui/test/AppShell.test.jsx`, so the token wiring is inherited, not independently re-verified here.
- **Full keyboard arrow-key traversal** for the tree/table (section 6's fuller interaction spec) — only basic focusability/labelling (checkbox labels, `aria-current`, `role="progressbar"`/`role="alert"`/`role="status"`) was added in this change, as scoped in `proposal.md` "Out of scope"; arrow-key neighbour traversal is left for the screens that wire these components to real, navigable data.
- **Integration into real screens** (Sources table, Add-source wizard, Run view) — out of scope per `proposal.md`; these are presentational components only, not wired to any route or data source in this change.
- **`docker compose up` / live container run** — not exercised in this session; `npx vite build` confirms the production bundle compiles, and the existing `ui/test/health.test.js` (unchanged) covers the `/health` endpoint contract, but no container was actually started.
