# Verification

Status: PASS
Date: 2026-10-31   Commit: 69bc47aca8bbffa29444b1451166c7699e6827d3

## Checks
| Check | Result |
|---|---|
| Lint | No linter configured in the repo yet (no `ruff`/`eslint` config); none run |
| Tests (full suite) | `api`: 1/1 pytest passed. `scheduler`: 1/1 pytest passed. `ui`: 1/1 node:test passed |
| docker compose up exercised | Yes, on Windows (Docker Desktop, WSL2 backend) — see below |
| contract-check | No schema, ontology, harvester-interface, adapter or MCP changes in this diff; no cloud SDK imports found; not applicable |
| Definition of Done | All tasks ticked except task 8 (Linux run), explicitly deferred below |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Compose stack starts all services / compose-up-windows-wsl2 | `docker compose up -d --build` on this host (Windows 11, Docker Desktop WSL2 backend); `docker compose ps` showed all 5 containers | PASS |
| Compose stack starts all services / compose-up-linux | Not run — no Linux Docker host available in this session | NOT VERIFIED (see below) |
| Every service reports health / compose-up-windows-wsl2 | `docker compose ps` output: `api` healthy, `embeddings` healthy, `postgres` healthy, `scheduler` healthy, `ui` healthy (after overriding `UI_PORT` to avoid a local port 3000 conflict) | PASS |
| Every service reports health / healthcheck-reports-unhealthy-before-ready | `docker compose restart api` then `docker inspect --format '{{.State.Health.Status}}' <api container>` immediately returned `starting`, not `healthy` | PASS |
| Postgres has pgvector enabled / compose-up-windows-wsl2 | `docker compose exec postgres psql -U context -d context -c "\dx"` listed `vector 0.8.7` | PASS |
| README setup verified cross-platform / readme-verified-windows-wsl2 | Followed README "Local setup" steps verbatim on this host: `cp .env.example .env`, `docker compose up`, `curl` against `/health` on api (8000), scheduler (8001), ui (3000/3100) all returned `{"status":"ok"}` | PASS |
| README setup verified cross-platform / readme-verified-linux | Not run — no Linux host available in this session | NOT VERIFIED (see below) |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| `docker compose up` starts all services locally on Windows (WSL2) and Linux | compose-up-windows-wsl2 (PASS), compose-up-linux (NOT VERIFIED) | PARTIAL |
| Health checks | compose-up-windows-wsl2, healthcheck-reports-unhealthy-before-ready | PASS |
| README steps verified | readme-verified-windows-wsl2 (PASS), readme-verified-linux (NOT VERIFIED) | PARTIAL |

## Not verified
- **Linux**: `docker compose up` was not run on a Linux Docker host in this session (only a Windows + Docker Desktop WSL2 host was available). The compose file and all five service images use no OS-specific paths or constructs, so behaviour is expected to be identical, but this has not been directly exercised. Deferred to a CI job on `ubuntu-latest` that runs `docker compose up` and checks `/health` on each service, to be added in KAN-5 (per Build order: "Epic 1 Foundation ... CI"). Accepted as a known gap for this story per user direction; not a blocker for opening the PR, but the PR must not be merged until this is closed or formally waived.
