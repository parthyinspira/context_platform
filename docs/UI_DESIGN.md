# UI design spec

Status: specification for the hi-fi design. Figma files are not produced from this repo; see "Path to Figma-level design" at the end.

## 1. Principles
1. **Show the work.** Every number and node links to its source and run.
2. **Safe by default.** Destructive or expensive actions (run, widen scope) show an estimate and need confirmation.
3. **Calm density.** Information-dense but quiet; colour is used for meaning, not decoration.
4. **The graph is the hero.** Everything else supports getting to, trusting and explaining the graph.

## 2. Design tokens (single source: `ui/src/tokens.json`, used by code and Figma variables)

**Colour (light, with dark counterparts)**
| Token | Light | Use |
|---|---|---|
| `bg.canvas` | #F7F8FA | app background |
| `bg.surface` | #FFFFFF | cards, panels |
| `border.subtle` | #E3E6EB | dividers |
| `text.primary` | #14171F | body |
| `text.secondary` | #5B6270 | labels, help |
| `accent` | #4F46E5 | primary action, selection |
| `success / warning / danger` | #1E8E5A / #B7791F / #C53030 | run and validation status, always paired with an icon and label |

**Graph encoding (colour by family, shape/icon by type, never colour alone)**
| Family | Types | Colour |
|---|---|---|
| Code | Repository, Module, Job, Service | indigo |
| Data | Table, Column | teal |
| BI | Dashboard | amber |
| Documents | Document | slate blue |
| People | Person, Team | rose |
Palette to be validated for colour-blind safety and contrast (WCAG AA) during build.

**Type:** Inter (UI), JetBrains Mono (code, IDs). Scale 12 / 14 / 16 / 20 / 28. **Spacing:** 4-pt grid (4, 8, 12, 16, 24, 32). **Radius:** 6 (controls), 10 (cards). **Elevation:** 2 levels. **Motion:** 120 to 200 ms ease-out; respects reduced-motion.

## 3. App shell
Left rail: Graph, Sources, Runs, Agents, Settings. Top bar: global search (`/`), environment badge, user. Content area uses 12-column layout; right-hand inspector panel opens on selection.

## 4. Screens

### 4.1 Knowledge graph (home)
- Force-directed canvas (Cytoscape.js). Nodes: size by degree, colour by family, shape by type, label on zoom or hover.
- Left filter panel: source, entity type/family, relation, freshness, text search with result list; toggles for "show tombstoned" and "show unresolved".
- Interactions: pan/zoom, click to select (neighbours highlighted, others dimmed), double-click to expand neighbours (depth 1), shift-click multi-select, path finder between two nodes, lineage mode (up/down arrows, depth slider), minimap, legend, fit and reset.
- Inspector (right): entity card with properties, edges grouped by relation, citations (source link, `harvested_at`, run id), owner, "open in source".
- Scale rules: cap rendered nodes (for example 2,000) with clustering by source and type; expand on demand; level-of-detail labels; layout cached; empty state offers "Add a source".
- Agent overlay: nodes an agent retrieved pulse and are numbered in retrieval order.

### 4.2 Sources
Table: name, type, scope summary, last run, next run, validation badge, owner, actions (Run, Edit scope, Pause). Row expand shows the last 5 runs. Empty state with source-type tiles.

### 4.3 Add-source wizard (5 steps, stepper with save-and-resume)
1. **Type** (tiles: Git, SQL database, Upload, SharePoint, Snowflake, Tableau; unbuilt ones show "Coming soon").
2. **Connect:** credential form per type, "Test connection", masked secrets, read-only reminder.
3. **Discover:** scope tree with checkboxes and per-node size/count; search; "select recommended" button.
4. **Plan:** the harvest plan preview: what will be pulled and skipped (by type and size), estimated bytes, files, time and LLM tokens, budgets, stack detections (for example "Talend project detected: pulling `.item`, `.properties`; skipping 9.4 GB of binaries"). Editable include/exclude rules; warnings when over budget.
5. **Review and run:** summary, schedule, **Run now**.

### 4.4 Run view
Stage timeline (Connect to Publish) with live counts, log stream, budgets as meters (files, bytes, time, tokens), stop button. Finishes in PUBLISHED, QUARANTINED or FAILED with next-step guidance and a link to the report.

### 4.5 Validation report
Overall badge (PASS / WARN / FAIL) and a check list (completeness, exclusion integrity, budgets, parse success, expected yield, ontology conformance, delete sanity, secrets/PII, freshness), each with counts and sample failures. Quarantined runs show "previous knowledge remains published".

### 4.6 Agents
Pick agent (workflow, research, prod support, call centre), enter a task, watch steps and knowledge-base calls, final answer with citations; clicking a citation opens the node on the graph. Side-by-side "with / without knowledge base" toggle for the demo.

### 4.7 Settings
Provider configuration (LLM, embeddings), default budgets, sensitivity labels, API tokens for MCP.

## 5. Component inventory
App shell, nav rail, global search, data table, status badge, stepper, scope tree, plan summary card, meter, stage timeline, log viewer, toast, confirm dialog, filter panel, graph canvas, legend, minimap, inspector panel, entity card, citation chip, empty state, skeleton loaders, error banner, key-value list, code/ID chip with copy.

## 6. States and quality bar
- Every screen defines **empty, loading (skeleton), error, partial and success** states.
- Accessibility: keyboard navigation for tree, table and graph (arrow-key neighbour traversal), visible focus, AA contrast, no colour-only meaning, screen-reader labels, a list view alternative to the graph.
- Performance budget: first graph paint under 2 s with 2,000 nodes; interactions under 100 ms.
- Responsive: designed for 1280 px and up; tablet usable; mobile out of scope.

## 7. Path to Figma-level design
This repo cannot create Figma files directly. Recommended path:
1. This spec plus `ui/src/tokens.json` is the source of truth.
2. Build a **hi-fi clickable prototype** (React, Tailwind, shadcn/ui, Cytoscape) with seeded demo data, using the tokens. It runs from `docker compose up`.
3. Bring it into Figma as variables and components (a plugin such as html.to.design, or manual recreation by a designer), or use a Figma-capable tool of yours, then iterate there.
4. Review screens against sections 4 to 6 before building the real data wiring.
