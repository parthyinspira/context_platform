# Capability: retrieval MCP

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

### Requirement: Tombstones excluded
Tombstoned entities SHALL NOT be returned.
#### Scenario: deleted object
- **Given** an entity with `tombstoned_at` set
- **When** it is searched
- **Then** it is not returned
