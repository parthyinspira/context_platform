# KAN-59: Component library: badge, table, stepper, scope tree, meter, timeline, empty/loading/error states

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-59   Epic: 6 Retrieval MCP / UI build-out   Branch: kepler/kan-59-component-library-badge-table

## Why
`docs/UI_DESIGN.md` section 5 lists the component inventory the later screens (Sources table, Add-source wizard stepper/scope tree, Run view meter/timeline) depend on. Today only the app shell (`NavRail`, `TopBar`) exists (`spec/capabilities/ui.md`). None of the data-bearing components exist yet, and section 6 requires every screen (so every component that stands in for screen content) to define empty, loading, error and success states. Building these now, with shared state primitives, unblocks the screens that reuse them without each screen re-inventing its own skeleton/empty/error handling.

## What changes
- Add shared state-rendering components used across the library: `EmptyState`, `Skeleton`, `ErrorBanner` (inventory items from `UI_DESIGN.md` section 5).
- Add six data-bearing components from the section 5 inventory, each accepting a `state` prop (`"empty" | "loading" | "error" | "success"`) and rendering the shared primitives for the first three and real content for `"success"`:
  - `Badge` (status badge: success/warning/danger/info variants, paired icon + label per section 2's "never colour alone" rule)
  - `DataTable` (generic column/row table, used later by the Sources screen)
  - `Stepper` (step list with save-and-resume affordance, used later by the Add-source wizard)
  - `ScopeTree` (checkbox tree with per-node count, used later by the Add-source wizard "Discover" step)
  - `Meter` (labelled progress bar against a budget, used later by the Run view)
  - `Timeline` (stage timeline Connect -> Publish, used later by the Run view)
- All new components consume `ui/src/tokens.json` colours/spacing/radius via the existing Tailwind token mapping (`ui/tailwind.config.js`) — no new hard-coded colours.
- Tests (Vitest + Testing Library) for every component's four states, mirroring `ui/test/AppShell.test.jsx`.

## In scope
- The 9 components above (6 primary + 3 shared primitives) as presentational components with mock/sample data passed by the caller; no data fetching, routing, or screen wiring.
- Keyboard focus visibility and `aria-live`/`aria-label` basics per section 6's accessibility bar (visible focus, no colour-only meaning, screen-reader labels) for the states that are new in this change.

## Out of scope
- Wiring these components into the actual screens (Sources, Add-source wizard, Run view) — that is each screen's own story in epic 6+.
- Full keyboard arrow-key tree/table/graph traversal (section 6) — only basic focusability/labelling is covered here; the fuller interaction spec is for the screens that use these components with real data and selection state.
- `plan summary card`, `log viewer`, `toast`, `confirm dialog`, `filter panel`, `graph canvas`, `legend`, `minimap`, `inspector panel`, `entity card`, `citation chip`, `key-value list`, `code/ID chip with copy` — other section 5 inventory items not named in this story's title; left for later stories.
- Dark-theme-specific visual QA beyond the existing token wiring (components use token CSS vars already proven to switch via `ui/src/theme.js`, covered by `ui/test/AppShell.test.jsx`).

## Acceptance criteria (from Jira)
"components match UI_DESIGN.md section 5; each has empty, loading, error and success states."
1. Components match `UI_DESIGN.md` section 5 -> scenarios: badge-variants, table-columns-rows, stepper-steps, scope-tree-nodes, meter-value, timeline-stages (one per component, confirming it renders the inventory item's described shape using design tokens)
2. Each has empty, loading, error and success states -> scenarios: `<component>-empty`, `<component>-loading`, `<component>-error`, `<component>-success` for all 6 primary components (24 scenarios) plus the 3 shared primitives (`EmptyState`, `Skeleton`, `ErrorBanner`) rendering correctly on their own

## Affected
Capabilities: `spec/capabilities/ui.md` (MODIFIED — new component inventory requirement)   Docs/contracts: none (no schema/ontology/harvester/MCP contract touched; `ui/src/tokens.json` is read, not changed)

## Risks and open questions
- No design review/Figma exists for these components (per `UI_DESIGN.md` section 7, this repo cannot produce Figma files); "matches section 5" is verified against the textual component inventory and the token system, not a visual mock.
- `Badge`, `Meter`, `Stepper` having a `"loading"/"error"/"empty"` data-state (versus just a `"success"`-only status indicator) is an interpretation of "each has empty, loading, error and success states" applied uniformly across every named component, since the Jira AC does not exempt any of them.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR.
