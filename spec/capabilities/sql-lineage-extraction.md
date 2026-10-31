# Capability: SQL lineage extraction

### Requirement: Deterministic SQL lineage extraction
The system SHALL extract table-level `READS_FROM` and `WRITES_TO` facts from SQL text using deterministic parsing (`sqlglot`), without calling an LLM, and SHALL emit `Table` entities and edges shaped to Ontology v0 (`type`, `source_id`, `external_id`, `ontology_version` on entities; `src_entity_id`, `dst_entity_id`, `relation`, `confidence`, `source_id`, `ontology_version` on edges).

#### Scenario: reads-from-select
- **Given** a SQL statement `SELECT a, b FROM schema.orders JOIN schema.customers ON ...`
- **When** it is extracted
- **Then** `Table` entities are produced for `schema.orders` and `schema.customers`, and a `READS_FROM` edge is produced from a query/statement entity to each table

#### Scenario: writes-to-insert-select
- **Given** a SQL statement `INSERT INTO schema.summary SELECT ... FROM schema.orders`
- **When** it is extracted
- **Then** a `WRITES_TO` edge is produced to `schema.summary` and a `READS_FROM` edge is produced from `schema.orders`

#### Scenario: writes-to-ctas
- **Given** a `CREATE TABLE schema.report AS SELECT ... FROM schema.orders` statement
- **When** it is extracted
- **Then** a `WRITES_TO` edge targets `schema.report` and a `READS_FROM` edge targets `schema.orders`

#### Scenario: multi-statement-script
- **Given** a `;`-separated SQL script containing multiple statements, including one unparseable statement
- **When** it is extracted
- **Then** edges are produced for every parseable statement, and the unparseable statement is reported in an `unparsed` list with its raw text and error, not silently dropped

### Requirement: Spike outcome documented
A time-boxed spike story SHALL produce a short written outcome (what works, limitations found, and a recommendation) in the change folder, in place of production-ready code for every edge case.

#### Scenario: spike-outcome-doc
- **Given** the KAN-25 spike is complete
- **When** the change folder is reviewed
- **Then** `design.md` states what `sqlglot`-based extraction handles, the limitations found during the spike, and a recommendation for adopting it in the Epic 5 ontology updater
