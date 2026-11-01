# UI

## Requirements

### Requirement: UI app shell with design tokens
The `ui` service SHALL be a React application built with Vite, styled with Tailwind CSS driven by `ui/src/tokens.json`, and served as static files; the running app SHALL render an app shell with a left nav rail (Graph, Sources, Runs, Agents, Settings) and a top bar, and SHALL support switching between a light and a dark theme sourced from `ui/src/tokens.json`.

#### Scenario: tokens-loaded-light-dark
- **Given** `ui/src/tokens.json` defines both a `light` and a `dark` token set
- **When** the app starts
- **Then** the rendered page applies the `light` token set's values by default and the `dark` token set's values are available for the dark theme

#### Scenario: app-shell-nav-rail-topbar
- **Given** the built app is rendered
- **When** the shell mounts
- **Then** a nav rail with the five nav items and a top bar are present in the DOM

#### Scenario: theme-toggle-switches-tokens
- **Given** the app is showing the light theme
- **When** the user activates the theme toggle in the top bar
- **Then** the app switches to the dark theme's token values (e.g. `data-theme="dark"` on the root element) and back on a second activation

#### Scenario: ui-compose-health
- **Given** the `ui` service image built from `ui/Dockerfile`
- **When** the container is run (standalone, or via `docker compose up`)
- **Then** it serves the built app on its configured port and `/health` returns 200

### Requirement: Sources screen lists sources and runs the dispatcher
The `ui` app SHALL provide a Sources screen, reachable from the nav rail, that calls `GET /sources` and renders each source's name (`uri`), type, status, last run and a validation badge, with a **Run** action for each `active` source. Activating **Run** for a source SHALL call `POST /sources/{id}/run` on the scheduler service and, on success, navigate to a run view showing the returned run id, source id and status. When `GET /sources` returns no rows, the screen SHALL show an empty state instead of a table.

#### Scenario: sources-list-renders
- **Given** `GET /sources` returns one or more sources
- **When** the Sources screen loads
- **Then** each source's name, type, status, last run and validation badge are rendered, and an active source has a Run action

#### Scenario: sources-list-empty-state
- **Given** `GET /sources` returns zero sources
- **When** the Sources screen loads
- **Then** an empty state is shown instead of a table

#### Scenario: sources-list-loading
- **Given** the `GET /sources` request has not yet resolved
- **When** the Sources screen mounts
- **Then** a loading state is shown

#### Scenario: sources-list-error
- **Given** `GET /sources` fails
- **When** the Sources screen loads
- **Then** an error state is shown instead of a table or empty state

#### Scenario: run-button-calls-dispatcher-and-navigates
- **Given** the Sources screen lists an active source
- **When** the user activates that source's Run action and `POST /sources/{id}/run` succeeds
- **Then** the dispatcher endpoint is called with that source's id, and the screen navigates to a run view showing the returned run id, source id and status

#### Scenario: run-button-error-stays-on-sources
- **Given** the Sources screen lists an active source
- **When** the user activates that source's Run action and `POST /sources/{id}/run` fails
- **Then** the screen stays on the Sources list and shows an error message, without navigating

### Requirement: Shared state-rendering primitives
The `ui` service SHALL provide shared `EmptyState`, `Skeleton` and `ErrorBanner` components driven by `ui/src/tokens.json`, for reuse by any data-bearing component that needs an empty, loading or error state.

#### Scenario: empty-state-renders-message-and-action
- **Given** an `EmptyState` with a message and an optional action label
- **When** it is rendered
- **Then** the message is shown and, if provided, the action button is shown

#### Scenario: skeleton-renders-without-content
- **Given** a `Skeleton` with a shape (`row` or `block`) and a count
- **When** it is rendered
- **Then** that many skeleton placeholders are shown and no real content is rendered

#### Scenario: error-banner-renders-message
- **Given** an `ErrorBanner` with an error message
- **When** it is rendered
- **Then** the message is shown with the `danger` token colour and an icon, not colour alone

### Requirement: Component library matches UI_DESIGN.md section 5
The `ui` service SHALL provide `Badge`, `DataTable`, `Stepper`, `ScopeTree`, `Meter` and `Timeline` components matching the shapes described in `UI_DESIGN.md` section 5, each accepting a `state` prop of `"empty" | "loading" | "error" | "success"` that renders, respectively, the shared `EmptyState`, `Skeleton`, `ErrorBanner` primitives or the component's real content.

#### Scenario: badge-variants
- **Given** a `Badge` with `state="success"` and a `variant` of `success`, `warning`, `danger` or `info`
- **When** it is rendered
- **Then** it shows the variant's token colour, an icon and a text label (not colour alone)

#### Scenario: badge-loading
- **Given** a `Badge` with `state="loading"`
- **When** it is rendered
- **Then** a skeleton placeholder is shown instead of a variant/label

#### Scenario: badge-error
- **Given** a `Badge` with `state="error"`
- **When** it is rendered
- **Then** an error indicator is shown instead of a variant/label

#### Scenario: badge-empty
- **Given** a `Badge` with `state="empty"`
- **When** it is rendered
- **Then** a muted "no status" placeholder is shown instead of a variant/label

#### Scenario: table-columns-rows
- **Given** a `DataTable` with `state="success"`, a list of columns and a list of rows
- **When** it is rendered
- **Then** a table with a header row for each column and one row per data row is shown

#### Scenario: table-loading
- **Given** a `DataTable` with `state="loading"`
- **When** it is rendered
- **Then** skeleton rows are shown instead of data rows

#### Scenario: table-error
- **Given** a `DataTable` with `state="error"` and an error message
- **When** it is rendered
- **Then** an error banner is shown instead of the table body

#### Scenario: table-empty
- **Given** a `DataTable` with `state="empty"`
- **When** it is rendered
- **Then** an empty state with a message is shown instead of the table body

#### Scenario: stepper-steps
- **Given** a `Stepper` with `state="success"`, a list of steps and an active step index
- **When** it is rendered
- **Then** each step is shown in order with the active step marked current and earlier steps marked complete

#### Scenario: stepper-loading
- **Given** a `Stepper` with `state="loading"`
- **When** it is rendered
- **Then** skeleton steps are shown instead of real steps

#### Scenario: stepper-error
- **Given** a `Stepper` with `state="error"`
- **When** it is rendered
- **Then** an error banner is shown instead of the step list

#### Scenario: stepper-empty
- **Given** a `Stepper` with `state="empty"` (no steps configured)
- **When** it is rendered
- **Then** an empty state with a message is shown instead of the step list

#### Scenario: scope-tree-nodes
- **Given** a `ScopeTree` with `state="success"` and a nested list of nodes, each with a label, a count and a checked flag
- **When** it is rendered
- **Then** each node is shown with its label, its count and a checkbox reflecting its checked state, nested under its parent

#### Scenario: scope-tree-loading
- **Given** a `ScopeTree` with `state="loading"`
- **When** it is rendered
- **Then** skeleton tree rows are shown instead of real nodes

#### Scenario: scope-tree-error
- **Given** a `ScopeTree` with `state="error"`
- **When** it is rendered
- **Then** an error banner is shown instead of the tree

#### Scenario: scope-tree-empty
- **Given** a `ScopeTree` with `state="empty"` (no nodes discovered)
- **When** it is rendered
- **Then** an empty state with a message is shown instead of the tree

#### Scenario: meter-value
- **Given** a `Meter` with `state="success"`, a `label`, a `value` and a `max`
- **When** it is rendered
- **Then** a labelled progress bar is shown filled to `value / max`, with the numeric value and max shown as text (not colour/fill alone)

#### Scenario: meter-loading
- **Given** a `Meter` with `state="loading"`
- **When** it is rendered
- **Then** a skeleton bar is shown instead of a filled progress bar

#### Scenario: meter-error
- **Given** a `Meter` with `state="error"`
- **When** it is rendered
- **Then** an error banner is shown instead of the progress bar

#### Scenario: meter-empty
- **Given** a `Meter` with `state="empty"` (no budget set)
- **When** it is rendered
- **Then** an empty state with a message is shown instead of the progress bar

#### Scenario: timeline-stages
- **Given** a `Timeline` with `state="success"` and an ordered list of stages, each with a name and a status (`pending`, `active`, `done`, `failed`)
- **When** it is rendered
- **Then** each stage is shown in order with its status indicated by an icon and label (not colour alone)

#### Scenario: timeline-loading
- **Given** a `Timeline` with `state="loading"`
- **When** it is rendered
- **Then** skeleton stage placeholders are shown instead of real stages

#### Scenario: timeline-error
- **Given** a `Timeline` with `state="error"`
- **When** it is rendered
- **Then** an error banner is shown instead of the stage list

#### Scenario: timeline-empty
- **Given** a `Timeline` with `state="empty"` (no run started)
- **When** it is rendered
- **Then** an empty state with a message is shown instead of the stage list

### Requirement: Entity card with citations (graph inspector)
The `api` service SHALL provide `GET /entities/{id}` returning the entity's `props`, its edges grouped by `relation` (each with the neighbour entity and direction `out`/`in`), the owning source's `owner` and `uri` (used for "open in source"), and a `citations` list — one per chunk on the entity — each with the source's `uri`, the chunk's `harvested_at`, and a best-effort `run_id` (the most recent `harvest_runs` row for the source at or before `harvested_at`, or `null` if no run matches). Tombstoned entities SHALL 404. The `ui` service SHALL provide an `EntityCard` component, matching `UI_DESIGN.md` 4.1's inspector, accepting a `state` of `"empty" | "loading" | "error" | "success"` that renders properties, edges grouped by relation, a citation per citation (source link, `harvested_at`, run id), the owner and an "open in source" link.

#### Scenario: entity detail grouped and cited
- **Given** an entity with two edges (one outgoing DEPENDS_ON, one incoming CONTAINS) and one chunk
- **When** `GET /entities/{id}` is called
- **Then** `edges_by_relation` has one entry per relation and `citations` has one entry with `source_link`, `harvested_at` and `run_id`

#### Scenario: tombstoned entity 404s
- **Given** a tombstoned entity id
- **When** `GET /entities/{id}` is called
- **Then** the response is 404

#### Scenario: entity card success
- **Given** an `EntityCard` with `state="success"` and entity data with props, grouped edges, citations and an owner
- **When** it is rendered
- **Then** all of these appear and the "open in source" link's `href` is the source uri

#### Scenario: entity card loading, error, empty
- **Given** an `EntityCard` with `state="loading"`, `"error"` or `"empty"`
- **When** it is rendered
- **Then** the shared `Skeleton`, `ErrorBanner` or `EmptyState` is shown instead of entity content

### Requirement: Add-source wizard type and connect steps
The `ui` app SHALL provide an `AddSourceWizard`, reachable from an "Add source" entry point on the Sources screen, whose step 1 renders one tile per source type from `UI_DESIGN.md` 4.3 (Git, SQL, Upload, SharePoint, Snowflake, Tableau) with only Git selectable (the rest disabled, labelled "Coming soon"), and whose step 2 renders a credential form for the selected type (for Git: repository URL and a masked `type="password"` credentials-ref/token field) with a "Test connection" button calling `POST /sources/test-connection`. A secret value, once accepted by a successful test or source creation, SHALL never be re-displayed in plain text on re-render.

#### Scenario: type tiles, only Git enabled
- **Given** the wizard opens at step 1
- **When** it renders
- **Then** six tiles are shown and only Git is enabled; selecting Git advances to step 2

#### Scenario: test connection success and error
- **Given** the connect form is filled in
- **When** "Test connection" is activated and the API returns `ok: true`
- **Then** a success indicator is shown; given `ok: false, error` instead, an error indicator with that message is shown

#### Scenario: test connection loading state
- **Given** "Test connection" is in flight
- **When** rendered
- **Then** a loading indicator is shown instead of a stale result

#### Scenario: secret never re-displayed
- **Given** a successful test connection
- **When** the step re-renders (e.g. navigating away and back)
- **Then** the secret field shows masked/blank content, not the original value

### Requirement: Add-source wizard discover scope-tree step
Once a source exists, the wizard's discover step SHALL call `POST /sources/{id}/discover` and render the result with the existing `ScopeTree` component (name, kind, size per node, nested under parent), with checkbox selection whose checked state propagates from a parent to its children and back (unchecking a child unchecks an otherwise-fully-checked parent), a search input that filters to name matches and their ancestors, and a "select recommended" action that checks every leaf node.

#### Scenario: scope tree renders with sizes
- **Given** discover returns a tree with children
- **When** the discover step renders
- **Then** nested nodes with their sizes are shown via `ScopeTree`

#### Scenario: checkbox propagation
- **Given** a parent with two children
- **When** the parent checkbox is toggled on
- **Then** both children become checked; when one child is then unchecked, the parent becomes unchecked

#### Scenario: search filters to matches and ancestors
- **Given** a tree with a node named "billing-service"
- **When** the user types "billing"
- **Then** that node and its ancestors remain visible and non-matching siblings are hidden

#### Scenario: select recommended
- **Given** no nodes are checked
- **When** "select recommended" is activated
- **Then** every leaf node becomes checked

### Requirement: Add-source wizard plan-preview and run step
The wizard's plan step SHALL call `POST /sources/{id}/plan` with the discover-step selection and render a `PlanSummaryCard` showing pulled-by-type counts and the plan's `include`/`exclude` patterns, the response's byte/file/time/token estimates as labelled values, and a visible warning (icon + text) per entry in a non-empty `budget_warnings` list. The `include`/`exclude` patterns SHALL be editable as a text list before running, with edits sent in the `POST /sources/{id}/runs` plan body instead of the original. "Run now" SHALL call `POST /sources/{id}/runs` with that plan and, on success, hand the created run to the app's run-view navigation; on failure an error is shown and the wizard stays on this step.

#### Scenario: plan summary shows pulled-by-type and patterns
- **Given** a plan response with `counts_by_type` and an exclude pattern
- **When** the plan step renders
- **Then** the pulled-by-type groups and the exclude pattern are shown

#### Scenario: estimates shown
- **Given** a plan response with estimated bytes, files, time and tokens
- **When** rendered
- **Then** all four values are shown with labels

#### Scenario: budget warnings
- **Given** a non-empty `budget_warnings` list
- **When** rendered
- **Then** a warning is shown per entry; given an empty list, no warning is shown

#### Scenario: edited patterns round-trip into the run
- **Given** the user adds an exclude pattern
- **When** "Run now" is activated
- **Then** the run-creation request body's plan includes the edited pattern

#### Scenario: run now navigates or shows an error
- **Given** a valid plan
- **When** "Run now" is activated and the API returns a run id
- **Then** the app navigates to the run view for that id; given the API call fails instead, an error is shown and the wizard stays on this step

### Requirement: Run view polls status and shows a stage timeline, log and budget meters
`RunView` SHALL poll `GET /runs/{id}` on an interval while the run is non-terminal, rendering a `Timeline` whose stages map from `HarvestRunState` with manifest-summary counts shown alongside, a scrollable log list with one line per manifest entry (`ref`, `outcome`, `outcome_reason`), and a `Meter` for each of files/bytes/time/tokens using the plan's budgets as `max` and the manifest's current counts as `value` (a `Meter` whose budget is unset renders `empty`). A "Stop" button, visible only while the run is non-terminal, SHALL call `PATCH /runs/{id}/stop` and reflect the resulting terminal state. Once terminal, the view SHALL show that state and a next-step action: a link to the validation report for `PUBLISHED`/`QUARANTINED`/`PARTIAL`, or back to Sources for `FAILED`.

#### Scenario: live stage and counts, polling stops at terminal state
- **Given** a run in state HARVESTING with manifest counts
- **When** `RunView` renders
- **Then** the Timeline shows Harvesting as active and the counts are shown; once the run reaches PUBLISHED, polling stops and Published is marked done

#### Scenario: log list
- **Given** a manifest with three entries
- **When** rendered
- **Then** three log lines are shown in entry order

#### Scenario: budget meters, empty when unset
- **Given** a plan with `max_files` set and a manifest with a fetched count
- **When** rendered
- **Then** a files Meter shows value/max; given `max_tokens` is null, the tokens Meter renders empty

#### Scenario: stop button
- **Given** a run in state HARVESTING
- **When** Stop is activated and the API succeeds
- **Then** the view shows the run as Failed with "stopped by user"; given the run is already terminal, no Stop button is shown

#### Scenario: terminal next steps
- **Given** state PUBLISHED
- **When** rendered
- **Then** a "View validation report" link is shown; given state FAILED instead, a "Back to sources" action is shown

### Requirement: Graph canvas renders entities as a force-directed, filterable graph
The `ui` app SHALL provide a `GraphCanvas` component (Cytoscape.js), rendered by a `GraphScreen` reachable from the nav rail's "Graph" item, that calls `GET /graph` and lays out the returned nodes/edges with Cytoscape's force-directed (`cose`) layout, colouring each node by its entity family and shaping it by its entity type per the family/type mapping in `ui/src/tokens.json` (driven by `UI_DESIGN.md` section 2's graph encoding table). The canvas SHALL support Cytoscape's default pan and zoom, click-to-select a node with neighbour highlighting (the tapped node's closed neighbourhood gets a `highlighted` style and all other elements get `dimmed`; tapping the background clears both), and explicit **Fit** (`cy.fit()`) and **Reset** (re-run the `cose` layout, fit, and clear any highlighting/dimming) controls. `GraphScreen` SHALL show the shared loading/empty/error states around the canvas while `GET /graph` is pending, fails, or returns no nodes.

#### Scenario: force-directed layout
- **Given** `GET /graph` returns nodes and edges
- **When** `GraphCanvas` mounts
- **Then** cytoscape initializes with `layout.name === "cose"`

#### Scenario: colour by family, shape by type
- **Given** a node of type `Repository`
- **When** it is rendered
- **Then** its style rule maps the `Repository` type's family to that family's colour token and the `Repository` type to its shape token

#### Scenario: select highlights neighbourhood, background clears it
- **Given** a rendered graph
- **When** a node is tapped
- **Then** its closed neighbourhood gets `highlighted` and the rest get `dimmed`; when the background is tapped instead, both classes are cleared

#### Scenario: fit and reset
- **Given** a rendered graph
- **When** Fit is activated
- **Then** `cy.fit()` runs; when Reset is activated instead, the layout re-runs, the view fits, and any highlighting/dimming clears

#### Scenario: graph screen loading, empty and error states
- **Given** `GET /graph` is pending, fails, or returns no nodes
- **When** `GraphScreen` renders
- **Then** the loading, error, or empty state is shown instead of the canvas, respectively

### Requirement: Validation report screen
The `ui` app SHALL provide a validation report screen, reachable from `RunView`'s "View validation report" action, that fetches `GET /runs/{id}/validation` and `GET /runs/{id}` (for `state`) and renders an overall `Badge` for the report's `status` (PASS/WARN/FAIL, using the existing success/warning/danger variant mapping), one row per entry in the report's `checks` list (name, message, counts as a key-value list, samples as a list or "none" when empty), a quarantine-explanation panel when the run's `state` is `QUARANTINED`, and — when `GET /runs/{id}/validation` returns 404 (no report yet) — an informative fallback using the run's `state` and `error` instead of a bare error screen.

#### Scenario: status badge
- **Given** a report with status "FAIL"
- **When** the screen renders
- **Then** the Badge shows the danger variant and "FAIL" text

#### Scenario: checks with counts and samples
- **Given** a report with two checks, one with samples and one without
- **When** rendered
- **Then** both checks are listed with their counts, and the one with no samples shows "none" rather than an empty block

#### Scenario: quarantine explanation
- **Given** state QUARANTINED
- **When** rendered
- **Then** the quarantine explanation panel is shown; given state PUBLISHED instead, it is not shown

#### Scenario: 404 fallback
- **Given** a 404 from the validation endpoint and a run with `state=FAILED, error="connect failed: ..."`
- **When** rendered
- **Then** that state and error are shown as the fallback content, not a generic error state
