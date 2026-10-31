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
