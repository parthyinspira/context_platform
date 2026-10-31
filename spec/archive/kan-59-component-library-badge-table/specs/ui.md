# Delta for ui

## ADDED Requirements

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
