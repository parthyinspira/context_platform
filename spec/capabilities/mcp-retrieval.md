# Capability: retrieval MCP

### Requirement: Hybrid search
The service SHALL combine keyword (PostgreSQL tsvector) and vector (pgvector cosine) rankings via Reciprocal Rank Fusion (RRF, k=60). Callers MAY filter by `source_ids`, `entity_types`, and `sensitivities`.
#### Scenario: hybrid search with metadata filter
- **Given** indexed chunks with sensitivity "public" and "restricted"
- **When** `GET /search?q=...&sensitivities=public` is called
- **Then** only public-source chunks are returned, each with source_link, harvested_at, sensitivity and score

### Requirement: Cited results
Every retrieval result SHALL include source link, `harvested_at` and `sensitivity`.
#### Scenario: search
- **Given** indexed content
- **When** `search_context` is called
- **Then** each result carries source link, harvested_at and sensitivity

### Requirement: Sensitivity filtering
The service SHALL filter results by the caller's allowed sensitivity and source access; restricted sources SHALL NOT appear in results or error messages.
#### Scenario: restricted document
- **Given** a restricted document and a caller without access
- **When** the caller searches for its content
- **Then** it is not returned and not hinted at

### Requirement: Lineage traversal
`get_lineage` SHALL traverse READS_FROM, WRITES_TO and DERIVED_FROM edges up to a depth limit and return the path with citations.
#### Scenario: downstream
- **Given** a table feeding a job feeding a dashboard
- **When** `get_lineage(table, downstream, 3)` is called
- **Then** the job and the dashboard are returned with their edges

### Requirement: Related entity traversal
`get_related` SHALL traverse `edges` up to a caller-supplied depth limit (default 3, max 10) via a recursive CTE, following outbound, inbound, or both edge directions. It SHALL return each reachable entity (excluding tombstoned) with the connecting relation label and a citation (source_link, harvested_at, sensitivity, confidence). An optional relation filter restricts which edge labels are followed.
#### Scenario: two-hop traversal
- **Given** entity A connected by DEPENDS_ON to B, and B connected by READS_FROM to C
- **When** `get_related(A, depth=2)` is called
- **Then** B and C are returned, each with their connecting relation and citation fields

### Requirement: Tombstones excluded
Tombstoned entities SHALL NOT be returned.
#### Scenario: deleted object
- **Given** an entity with `tombstoned_at` set
- **When** it is searched
- **Then** it is not returned
