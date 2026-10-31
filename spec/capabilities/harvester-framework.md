# Capability: harvester framework

### Requirement: Lifecycle
A harvester SHALL implement connect, discover, profile, plan, harvest, normalize and validate, and each run SHALL record its state in `harvest_runs`.
#### Scenario: full run
- **Given** an approved plan
- **When** a run executes
- **Then** states progress CONNECTING to PUBLISHED or QUARANTINED, each recorded

### Requirement: Discover before download
A harvester SHALL list and size objects before fetching content and SHALL fetch only objects allowed by the plan.
#### Scenario: large repository
- **Given** a 10 GB repository whose logic is in a few `.item` files
- **When** the plan is built
- **Then** only planned paths are fetched and skipped paths are listed in the manifest with reasons

### Requirement: Budgets
A run SHALL enforce budgets for files, bytes, time and tokens; on exceeding one it SHALL stop cleanly and mark the run PARTIAL.
#### Scenario: budget hit
- **Given** a file budget of 1000
- **When** the 1001st file would be fetched
- **Then** the run stops, is marked PARTIAL, and the report names the budget

### Requirement: Metadata first
A harvester SHALL NOT pull row data by default; samples SHALL be opt-in and capped.
#### Scenario: database source
- **Given** a SQL database source with default settings
- **When** it is harvested
- **Then** only catalog metadata is stored

### Requirement: Read-only and secret-safe
A harvester SHALL use read-only credentials and SHALL redact detected secrets before storage.
#### Scenario: secret in a file
- **Given** a file containing an API key
- **When** it is harvested
- **Then** the key is redacted in stored text and the object is marked sensitive

### Requirement: Idempotent incremental runs
Re-running a harvest SHALL NOT create duplicates and SHALL only process changes since the cursor.
#### Scenario: rerun unchanged
- **Given** a completed harvest
- **When** it is run again with no source changes
- **Then** no entities are created or changed

### Requirement: Fixture set for harvester tests
The project SHALL provide a deterministic, non-sensitive fixture set under `fixtures/` covering every stack and source type named in `docs/HARVESTERS.md`, so harvester and MCP tests do not depend on live external sources.

#### Scenario: sql-dbt-fixture-present
- **Given** the repo at `fixtures/repos/sql-dbt-sample/`
- **When** it is listed
- **Then** it contains a source table definition, a staging model and a mart model forming one lineage chain, plus a `schema.yml`

#### Scenario: java-fixture-present
- **Given** the repo at `fixtures/repos/java-sample/`
- **When** it is listed
- **Then** it contains a `pom.xml`, `src/main/java/**/*.java`, a SQL resource, and a `target/` directory that a harvester must skip

#### Scenario: dotnet-fixture-present
- **Given** the repo at `fixtures/repos/dotnet-sample/`
- **When** it is listed
- **Then** it contains a `.sln`, a `.csproj`, `*.cs` files, `appsettings.json`, and `bin/`/`obj/` directories that a harvester must skip

#### Scenario: talend-fixture-present
- **Given** the repo at `fixtures/repos/talend-sample/`
- **When** it is listed
- **Then** it contains small `.item`/`.properties` job files and dummy binary/screenshot files larger than the 1 MB per-object size cap in `docs/HARVESTERS.md`, so a harvest plan must include the job files and skip the binaries

#### Scenario: postgres-fixture-present
- **Given** `fixtures/db/init.sql`
- **When** it is applied to an empty Postgres database
- **Then** it creates schemas, tables, a view, a stored procedure, column/table comments, and seed rows consistent with the dbt lineage chain, including one table flagged as stale for prod-support test scenarios

#### Scenario: docs-fixture-present
- **Given** `fixtures/docs/`
- **When** it is listed
- **Then** it contains at least one policy document and one FAQ document, with one document's front matter marked `sensitivity: internal` and another marked `sensitivity: restricted`

#### Scenario: excel-fixture-present
- **Given** `fixtures/docs/`
- **When** it is listed
- **Then** it contains at least one `.xlsx` file with named sheets, headers and a few sample rows

#### Scenario: secret-scan-clean
- **Given** the `fixtures/` tree
- **When** the `secret-scan` skill is run over it
- **Then** the only match is the single documented, clearly-fake secret placed in `fixtures/repos/talend-sample/` for future redaction tests; no other secret-shaped value is present

#### Scenario: fixtures-documented
- **Given** `fixtures/EXPECTED.md`
- **When** it is read
- **Then** it lists, per fixture, the entities and edges (per the Ontology v0 types in `CLAUDE.md`) a harvester is expected to extract, so harvester tests can assert against it

#### Scenario: fixtures-regeneration-deterministic
- **Given** `scripts/generate_fixtures.py`
- **When** it is run twice against a clean output directory
- **Then** the two runs produce byte-identical file trees
