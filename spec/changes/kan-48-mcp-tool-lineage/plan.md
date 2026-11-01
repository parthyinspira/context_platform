# KAN-48: MCP tool get_lineage (upstream/downstream) (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-48   Branch: kepler/kan-48-mcp-tool-lineage-upstream

## Scope
In: `GET /lineage/{entity_id}?direction=downstream|upstream&depth=N` REST endpoint that traverses READS_FROM/WRITES_TO/DERIVED_FROM edges using a recursive CTE and returns matched nodes with citations (source_link, harvested_at, sensitivity). Tombstoned entities excluded.
Out: A separate MCP server binary/container, `search_context`, sensitivity access-control filtering.

## Acceptance criteria (from Jira)
1. Depth-limited traversal over READS_FROM/WRITES_TO/DERIVED_FROM using recursive CTE.
2. Returns path with citations (source link, harvested_at, sensitivity).
3. Tombstoned entities are excluded from results.

## Requirements
- R1: `GET /lineage/{entity_id}` SHALL accept `direction` (upstream|downstream, default downstream) and `depth` (int, 1-10, default 5) parameters and traverse the graph using a recursive CTE; relations READS_FROM, WRITES_TO, DERIVED_FROM only. (Given table→job→dashboard graph, When `get_lineage(table, downstream, 3)`, Then job and dashboard returned with their edges.)
- R2: Each node in the response SHALL carry `source_link`, `harvested_at` and `sensitivity` as citations. (Given indexed entity with chunks, When lineage endpoint is called, Then each node includes citation fields.)
- R3: Entities with `tombstoned_at` set SHALL NOT appear in lineage results. (Given tombstoned entity in graph, When lineage traversal reaches it, Then it is excluded and traversal does not continue through it.)

## Tasks
- [x] 1. Write tests for R1 (basic downstream + upstream traversal), R2 (citations), R3 (tombstoned excluded) — test first
- [x] 2. Implement `api/app/schemas_lineage.py` and `api/app/routes_lineage.py` with recursive CTE
- [x] 3. Register lineage router in `api/app/main.py`

## Risks / not verifiable here
- Recursive CTE cycle-guard relies on visited array; Postgres supports it but array comparison is O(n). Fine for hackathon-scale graphs.
- `harvested_at` pulled from most-recent chunk per entity; if no chunks exist, it is null.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
