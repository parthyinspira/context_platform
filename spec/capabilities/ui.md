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
