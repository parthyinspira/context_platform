# Context Platform

Harvest enterprise sources (Git, databases, documents) into a knowledge graph plus vector store, and serve it to agents through MCP. Container-first: runs locally with Docker, deployable to GCP (hackathon) and Azure (later).

Start here: `CLAUDE.md`, then `docs/`:
- `docs/HACKATHON_SCOPE.md`: what is in and out
- `docs/ARCHITECTURE.md`: topology, hierarchy, MCP design, portability
- `docs/HARVESTERS.md`: harvester lifecycle, scoping rules, validator
- `docs/UI_DESIGN.md`: UI spec
- `docs/DEMO_AGENTS.md`: workflow, research, prod support and call-centre demos
- `docs/DEV_WORKFLOW.md`: dev agent plus reviewer agent per story

## Local setup (Windows, macOS, Linux)
1. Install Docker Desktop (WSL2 backend on Windows), Git, Python 3.12, Node 20+.
2. Clone into a short path, for example `C:\Hackathon\context_platform`.
   - Windows: `git config --global core.longpaths true`
3. `cp .env.example .env` and fill in the LLM endpoint and key (Meta Llama credits). Never commit `.env`.
4. `docker compose up` (the compose stack arrives with Epic 1, KAN-1 to KAN-5).

## Working on a story
1. Pick a Jira story in project `KAN`; branch `kan-<n>-short-slug`.
2. Build with Claude Code (VS Code); read the acceptance criteria and the docs above first.
3. Open a PR using the template; run the `story-reviewer` agent; fix blocking findings.
4. Merge; move the story to Done.

## Status
Documentation and design only. Next: Epic 1 Foundation (compose stack, Postgres + pgvector, adapter interfaces, CI).
