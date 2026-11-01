# KAN-66: Knowledge graph canvas (Cytoscape) (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-66   Branch: kepler/kan-66-knowledge-graph-canvas-cytoscape

## Scope
In: a `GraphCanvas` component (Cytoscape.js) and a `GraphScreen` wrapper wired into the nav rail's existing "Graph" view in `ui/`, rendering entities/relations as a force-directed graph coloured by family and shaped by type per `docs/UI_DESIGN.md` 4.1/2, with pan, zoom, click-to-select with neighbour highlight, fit, and reset. Adds a `GET /graph` client call (`ui/src/api.js`) and family/type-shape tokens (`ui/src/tokens.json`).
Out: filter panel, search, inspector panel, double-click expand, multi-select, path finder, lineage mode, minimap, legend, agent overlay, clustering/scale rules, the `/graph` backend endpoint itself (context service work, separate story). Loading/error/empty states reuse existing shared primitives.

## Acceptance criteria (from Jira)
1. Force-directed graph.
2. Colour by family and shape by type.
3. Pan, zoom, select with neighbour highlight.
4. Fit and reset.

## Requirements (only new or changed behaviour; at most 5)
- The system SHALL render graph nodes/edges with Cytoscape's force-directed (`cose`) layout (scenario: Given nodes and edges, When `GraphCanvas` mounts, Then cytoscape initializes with `layout.name === "cose"`).
- The system SHALL colour each node by its entity family and shape it by its entity type, per the family/type table in `docs/UI_DESIGN.md` (scenario: Given a `Repository` node, When rendered, Then its style rule maps family `Code` to the Code colour token and type `Repository` to its shape token).
- The system SHALL support pan/zoom (Cytoscape defaults) and click-to-select with neighbour highlighting, dimming non-neighbours (scenario: Given a rendered graph, When a node is tapped, Then its closed neighbourhood gets `highlighted` and the rest get `dimmed`; tapping the background clears both).
- The system SHALL provide Fit and Reset controls (scenario: Given a rendered graph, When Fit is activated, Then `cy.fit()` runs; When Reset is activated, Then the layout re-runs, the view fits, and highlighting/dimming clears).
- The `GraphScreen` SHALL show loading/empty/error states around the canvas using the existing shared primitives (scenario: Given `GET /graph` is pending/fails/returns no nodes, When the screen renders, Then the loading/error/empty state shows instead of the canvas).

## Tasks
- [x] 1. Add `GraphCanvas.test.jsx` (mocks `cytoscape`) covering layout, colour/shape mapping, fit, reset, select+neighbour-highlight, background clear, unmount cleanup (test first)
- [x] 2. Implement `GraphCanvas.jsx` and family/type tokens in `tokens.json`
- [x] 3. Add `GraphScreen.test.jsx` covering loading/success/empty/error, then implement `GraphScreen.jsx` and `api.getGraph()`
- [x] 4. Wire `GraphScreen` into `App.jsx`'s existing "graph" view
- [x] 5. Run full `ui` test suite and `vite build`; verify no regressions

## Risks / not verifiable here
- No real browser/visual check of the rendered canvas (jsdom has no canvas 2D context); cytoscape is mocked in unit tests. Interactive pan/zoom/select behaviour is verified at the wiring level (event handlers registered and invoked with expected effects), not via a live browser.
- `GET /graph` does not exist on the context service yet; `GraphScreen` is built against the endpoint shape `{ nodes: [{id,label,type}], edges: [{id,source,target,relation}] }` consistent with the ontology in `CLAUDE.md`. Wiring that endpoint is backend work for a separate story.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
