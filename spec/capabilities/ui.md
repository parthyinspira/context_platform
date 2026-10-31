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
