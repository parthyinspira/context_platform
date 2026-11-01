# KAN-31: Context service API (containerized) with hybrid search (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-31   Branch: kepler/kan-31-context-service-api-containerized

## Scope
In: hybrid search endpoint (keyword + vector, metadata filters), lineage traversal endpoint, get_entity and get_related endpoints, stateless FastAPI container, docker-compose entry, Dockerfile, unit tests.
Out: MCP protocol transport layer, auth/ACL, production cloud deploy scripts, embeddings generation (uses existing chunks table).

## Acceptance criteria (from Jira)
1. Keyword plus vector search with metadata filters (source_id, entity_type, sensitivity)
2. Stateless container (no local state, reads only from Postgres)
3. Runs under compose and in cloud (Dockerfile + compose service)

## Requirements (only new or changed behaviour)
- The system SHALL return hybrid search results combining keyword (tsvector) and vector (pgvector) scores using RRF, each result carrying source_link, harvested_at and sensitivity (Scenario: Given indexed chunks, When GET /search?q=..., Then results have citation fields and score)
- The system SHALL filter out tombstoned entities from all results (Scenario: Given entity with tombstoned_at set, When searched, Then not returned)
- The system SHALL filter by caller-supplied sensitivity list; chunks from excluded-sensitivity sources SHALL NOT appear (Scenario: Given restricted source, When caller omits its sensitivity, Then chunks excluded)
- The system SHALL traverse READS_FROM/WRITES_TO/DERIVED_FROM edges up to depth limit for GET /lineage/{entity_id} (Scenario: Given table->job->dashboard, When get_lineage(table, downstream, 3), Then job and dashboard returned)

## Tasks
- [x] 1. Write tests for hybrid search, sensitivity filter, tombstone exclusion, lineage (test first)
- [x] 2. Implement context_service/app/ (main.py, db.py, schemas.py, search.py, routes_search.py, routes_lineage.py, routes_entity.py)
- [x] 3. Add context_service/Dockerfile and context_service/requirements.txt
- [x] 4. Add context_service service to docker-compose.yml
- [x] 5. Update spec/capabilities/mcp-retrieval.md with hybrid search requirement

## Risks / not verifiable here
- Vector search requires actual embeddings in DB (integration test uses mocked data)
- Cloud deploy not verified (stateless container design satisfies the intent)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
