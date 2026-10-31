# KAN-101: Docker compose stack: Postgres+pgvector, API, UI, scheduler, embeddings

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-101   Epic: 1 Foundation   Branch: kan-101-docker-compose-stack

## Why
Epic 1 (Foundation) needs a working local container topology before any source registry, harvester or ontology work can start. Nothing currently runs: there is no `docker-compose.yml` and no `api/`, `ui/`, `scheduler/` or `embeddings/` service code in the repo. This story stands up the five foundation services as thin, healthy skeletons so later stories build business logic into containers that already start, link and report health.

## What changes
- Add `docker-compose.yml` defining five services: `postgres` (pgvector image), `api`, `ui`, `scheduler`, `embeddings`.
- Add a minimal skeleton app + Dockerfile for each of `api`, `ui`, `scheduler`, `embeddings`, each exposing a `/health` endpoint (or compose-level healthcheck equivalent) returning healthy once the container is ready.
- Configure Postgres with the `pgvector` extension enabled and a healthcheck (`pg_isready`).
- Wire service configuration from `.env` (per `.env.example`); no secrets committed.
- Update `README.md` "Local setup" with exact, verified steps for Windows (WSL2) and Linux, replacing the current placeholder step 4.

## In scope
- `docker-compose.yml` with the 5 services and healthchecks for each.
- One Dockerfile per non-Postgres service, with the smallest runtime that satisfies the service's eventual language per `docs/ARCHITECTURE.md` (API in Python, UI in Node, scheduler in Python, embeddings in Python).
- A `/health` (or compose `healthcheck`) per service that reports healthy only when the container's process is actually serving.
- Postgres container using a `pgvector`-enabled image, with a named volume and `pgvector` extension created on init.
- README steps verified end-to-end on both Windows (WSL2 backend) and Linux.

## Out of scope
- Any real business logic: source registry API routes, UI screens, dispatcher scheduling logic, embedding model inference. These containers are skeletons only (health endpoint + stated runtime), built out in Epics 2, 3, 4, 6.
- CI pipeline changes (not named in this story's AC; tracked separately if needed).
- Cloud deployment (GCP/Azure) — this story is local-only per the AC.
- `EventBus`, `ObjectStore`, `SecretStore` adapter implementations (later Epic 1 stories).
- MinIO or any object storage container (not named in the AC; `OBJECT_STORE=local` uses a bind-mounted folder, no extra container needed yet).

## Acceptance criteria (from Jira)
1. `docker compose up` starts all services locally on Windows (WSL2) and Linux -> scenarios: compose-up-linux, compose-up-windows-wsl2
2. Health checks -> scenarios: compose-up-linux, compose-up-windows-wsl2, healthcheck-reports-unhealthy-before-ready
3. README steps verified -> scenarios: readme-verified-linux, readme-verified-windows-wsl2

## Affected
Capabilities: `spec/capabilities/foundation.md` (new)   Docs/contracts: `README.md`, `.env.example` (ports/vars only, no values); no Confluence Contracts change (no schema/ontology/harvester interface touched).

## Risks and open questions
- Embeddings container needs a concrete local model choice (Ollama vs sentence-transformers) to build even a skeleton Dockerfile; `design.md` records the decision.
- Windows (WSL2) verification requires an actual WSL2 Docker Desktop environment; verification evidence will be gathered on whatever host is available at `spec-verify` time and noted if only one platform could be tested directly.
- Large base images (e.g. a full embedding model) could slow `docker compose up`; skeleton containers must not pre-download full models in this story.

## Changes during development
(none)

## Approval
Approved by: Parthasarathy Venkatachalam, 2026-10-31
