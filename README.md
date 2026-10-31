# Context Platform

Harvest enterprise sources (Git, databases, documents) into a knowledge graph plus vector store, and serve it to agents through MCP. Container-first: runs locally with Docker, deployable to GCP (hackathon) and Azure (later).

Start here: `CLAUDE.md`, then `docs/`:
- `docs/HACKATHON_SCOPE.md`: what is in and out
- `docs/ARCHITECTURE.md`: topology, hierarchy, MCP design, portability
- `docs/HARVESTERS.md`: harvester lifecycle, scoping rules, validator
- `docs/UI_DESIGN.md`: UI spec
- `docs/DEMO_AGENTS.md`: workflow, research, prod support and call-centre demos
- `docs/DEV_WORKFLOW.md`: dev agent plus reviewer agent per story

## Local setup (Windows WSL2, Linux)
Verified on both platforms for KAN-101 (compose stack: Postgres+pgvector, api, ui, scheduler, embeddings).

1. Install Docker Desktop (enable the WSL2 backend on Windows: Settings -> General -> "Use the WSL 2 based engine"), Git, Python 3.12, Node 20+.
2. Clone into a short path, for example `C:\Hackathon\context_platform` on Windows, or anywhere on Linux.
   - Windows: `git config --global core.longpaths true`
3. `cp .env.example .env`. The defaults work for `docker compose up` as-is (sample Postgres credentials, local adapters); fill in the LLM endpoint and key only when you need LLM-backed features. Never commit `.env`.
   - If a host port in `.env.example` (5432, 8000, 8001, 3000, 11434) is already in use on your machine, change the matching `*_PORT` variable in `.env` before starting.
4. `docker compose up` starts five services: `postgres` (Postgres 16 + pgvector), `api`, `scheduler`, `ui`, `embeddings` (Ollama).
5. Check status: `docker compose ps` should show all five services as `healthy` within about a minute (the `embeddings` service takes longest on first start).
6. Verify each service:
   - `curl http://localhost:8000/health` -> `{"status":"ok"}` (api)
   - `curl http://localhost:8001/health` -> `{"status":"ok"}` (scheduler)
   - `curl http://localhost:3000/health` -> `{"status":"ok"}` (ui)
   - `docker compose exec postgres psql -U context -d context -c "\dx"` -> lists the `vector` extension
7. `docker compose down -v` stops the stack and removes its volumes when you are done.

## Working on a story
1. Pick a Jira story in project `KAN`; branch `kan-<n>-short-slug`.
2. Build with Claude Code (VS Code); read the acceptance criteria and the docs above first.
3. Open a PR using the template; run the `story-reviewer` agent; fix blocking findings.
4. Merge; move the story to Done.

## Status
Epic 1 Foundation: compose stack done (KAN-101). Next: adapter interfaces, CI, source registry.
