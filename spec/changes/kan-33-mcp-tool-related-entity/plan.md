# KAN-33: MCP tool get_related(entity) (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-33   Branch: kepler/kan-33-mcp-tool-related-entity

## Scope
In: `get_related` MCP tool — depth-limited edge traversal via recursive CTE, returning entities with relation and citation (source_link, harvested_at, sensitivity). New `mcp_server/` package with Dockerfile and docker-compose service.
Out: other MCP tools (`search_context`, `get_entity`, `get_lineage`, `list_sources`), admin MCP, live MCPs, sensitivity-based ACL enforcement, pagination.

## Acceptance criteria (from Jira)
1. Traverses edges (depth-limited) via recursive CTE.
2. Returns entities with relation and citation.

## Requirements (only new or changed behaviour)
- The system SHALL implement a `get_related(entity_id, relation?, depth?, direction?)` MCP tool that traverses `edges` up to `depth` hops via a recursive CTE, returning each reachable entity (excluding tombstoned) with the relation that connected it and a citation (source_link, harvested_at, sensitivity).
  - Scenario: Given entity A→B (DEPENDS_ON)→C (READS_FROM), When `get_related(A, depth=2)` is called, Then B and C appear in the result with their connecting relations and citation fields.
- The system SHALL return an empty list (not an error) when the entity has no edges or the entity does not exist.

## Tasks
- [x] 1. Write unit tests for the recursive-CTE traversal logic (fake Postgres, same pattern as `api/tests/test_graph.py`)
- [x] 2. Implement `mcp_server/` package: `db.py`, `tools/get_related.py` (recursive CTE), `server.py` (JSON-RPC MCP endpoint)
- [x] 3. Add `mcp_server` service to `docker-compose.yml` and write `Dockerfile` + `requirements.txt`
- [x] 4. Update `spec/capabilities/mcp-retrieval.md` with the new requirement

## Risks / not verifiable here
- Docker build and live Postgres traversal not run (no Docker in CI); covered by unit tests with fake DB.
- MCP client interoperability (Claude Desktop, etc.) not tested; only JSON-RPC shape verified.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
