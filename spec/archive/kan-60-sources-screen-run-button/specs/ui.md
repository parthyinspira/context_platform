# UI (delta)

## ADDED Requirements

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
