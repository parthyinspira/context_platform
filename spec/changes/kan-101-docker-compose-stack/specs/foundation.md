# Delta for foundation

## ADDED Requirements

### Requirement: Compose stack starts all services
The system SHALL provide a `docker-compose.yml` that starts `postgres`, `api`, `ui`, `scheduler` and `embeddings` containers with a single `docker compose up` on both Windows (WSL2 backend) and Linux.

#### Scenario: compose-up-linux
- **Given** Docker Engine running on Linux with the repo cloned and `.env` populated from `.env.example`
- **When** `docker compose up` is run
- **Then** all five containers (`postgres`, `api`, `ui`, `scheduler`, `embeddings`) start without error

#### Scenario: compose-up-windows-wsl2
- **Given** Docker Desktop running on Windows with the WSL2 backend, the repo cloned and `.env` populated from `.env.example`
- **When** `docker compose up` is run
- **Then** all five containers start without error

### Requirement: Every service reports health
Each of the five services SHALL expose a health check that `docker compose ps` (or `docker inspect`) reports as `healthy` once the service is ready to serve, and that does not report healthy before then.

#### Scenario: compose-up-linux
- **Given** the stack started on Linux per the scenario above
- **When** each container finishes its startup
- **Then** `docker compose ps` shows `healthy` for `postgres`, `api`, `ui`, `scheduler` and `embeddings`

#### Scenario: compose-up-windows-wsl2
- **Given** the stack started on Windows WSL2 per the scenario above
- **When** each container finishes its startup
- **Then** `docker compose ps` shows `healthy` for all five services

#### Scenario: healthcheck-reports-unhealthy-before-ready
- **Given** a service container that has just started and has not yet opened its health endpoint
- **When** `docker compose ps` is checked immediately after start
- **Then** that service shows `starting` or `unhealthy`, never `healthy`, until it is actually ready

### Requirement: Postgres has pgvector enabled
The `postgres` service SHALL run a Postgres image with the `pgvector` extension available and created in the target database on first start.

#### Scenario: compose-up-linux
- **Given** the stack started on Linux
- **When** `CREATE EXTENSION IF NOT EXISTS vector;` is checked against the `postgres` service's database
- **Then** the extension is already installed and enabled

### Requirement: README setup verified cross-platform
`README.md` SHALL contain local setup steps that a developer can follow, unmodified, to reach a running stack on both Windows (WSL2) and Linux.

#### Scenario: readme-verified-linux
- **Given** a clean checkout on Linux
- **When** the README "Local setup" steps are followed exactly
- **Then** `docker compose up` succeeds and all services reach `healthy`

#### Scenario: readme-verified-windows-wsl2
- **Given** a clean checkout on Windows with Docker Desktop (WSL2 backend)
- **When** the README "Local setup" steps are followed exactly
- **Then** `docker compose up` succeeds and all services reach `healthy`
