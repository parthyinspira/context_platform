# Delta for foundation

## ADDED Requirements

### Requirement: Lint and test CI
The repository SHALL run lint and automated tests on every push and pull request against `main` via a CI workflow, covering the Python services (`api`, `scheduler`, `adapters`) and the UI service, plus a Linux `docker compose up` smoke test.

#### Scenario: ci-lint-runs
- **Given** a pull request with a Python lint violation in `api/`, `scheduler/`, or `adapters/`
- **When** the CI workflow runs
- **Then** the lint job fails, blocking a clean CI run

#### Scenario: ci-test-runs
- **Given** a pull request that changes `api/`, `scheduler/`, `adapters/`, or `ui/`
- **When** the CI workflow runs
- **Then** `pytest` runs for each Python service's `tests/` directory, `node --test` runs for `ui/test`, and the workflow fails if any test fails

#### Scenario: ci-compose-smoke-linux
- **Given** the CI workflow running on an `ubuntu-latest` runner
- **When** the compose-smoke-test job runs `docker compose up`
- **Then** all services reach healthy and each documented `/health` endpoint responds, closing the KAN-101 Linux verification gap

### Requirement: Project documentation entry point
`CLAUDE.md` SHALL document the system architecture, ontology v0 (entities and relations) and the harvester interface, kept in sync with the current repository state.

#### Scenario: claude-md-documents-contracts
- **Given** `CLAUDE.md` in the repository root
- **When** it is read
- **Then** it describes the container architecture, lists the ontology v0 entity and relation types, and gives the `Harvester` interface (`discover`, `fetch`, `normalize`)
