# Harvester framework — spec delta (KAN-88)

## ADDED Requirements

### Requirement: Fixture set for harvester tests
The project SHALL provide a deterministic, non-sensitive fixture set under `fixtures/` covering every stack and source type named in `docs/HARVESTERS.md`, so harvester and MCP tests do not depend on live external sources.

#### Scenario: sql-dbt-fixture-present
- **GIVEN** the repo at `fixtures/repos/sql-dbt-sample/`
- **WHEN** it is listed
- **THEN** it contains a source table definition, a staging model and a mart model forming one lineage chain, plus a `schema.yml`

#### Scenario: java-fixture-present
- **GIVEN** the repo at `fixtures/repos/java-sample/`
- **WHEN** it is listed
- **THEN** it contains a `pom.xml`, `src/main/java/**/*.java`, a SQL resource, and a `target/` directory that a harvester must skip

#### Scenario: dotnet-fixture-present
- **GIVEN** the repo at `fixtures/repos/dotnet-sample/`
- **WHEN** it is listed
- **THEN** it contains a `.sln`, a `.csproj`, `*.cs` files, `appsettings.json`, and `bin/`/`obj/` directories that a harvester must skip

#### Scenario: talend-fixture-present
- **GIVEN** the repo at `fixtures/repos/talend-sample/`
- **WHEN** it is listed
- **THEN** it contains small `.item`/`.properties` job files and dummy binary/screenshot files larger than the 1 MB per-object size cap in `docs/HARVESTERS.md`, so a harvest plan must include the job files and skip the binaries

#### Scenario: postgres-fixture-present
- **GIVEN** `fixtures/db/init.sql`
- **WHEN** it is applied to an empty Postgres database
- **THEN** it creates schemas, tables, a view, a stored procedure, column/table comments, and seed rows consistent with the dbt lineage chain, including one table flagged as stale for prod-support test scenarios

#### Scenario: docs-fixture-present
- **GIVEN** `fixtures/docs/`
- **WHEN** it is listed
- **THEN** it contains at least one policy document and one FAQ document, with one document's front matter marked `sensitivity: internal` and another marked `sensitivity: restricted`

#### Scenario: excel-fixture-present
- **GIVEN** `fixtures/docs/`
- **WHEN** it is listed
- **THEN** it contains at least one `.xlsx` file with named sheets, headers and a few sample rows

#### Scenario: secret-scan-clean
- **GIVEN** the `fixtures/` tree
- **WHEN** the `secret-scan` skill is run over it
- **THEN** the only match is the single documented, clearly-fake secret placed in `fixtures/repos/talend-sample/` for future redaction tests; no other secret-shaped value is present

#### Scenario: fixtures-documented
- **GIVEN** `fixtures/EXPECTED.md`
- **WHEN** it is read
- **THEN** it lists, per fixture, the entities and edges (per the Ontology v0 types in `CLAUDE.md`) a harvester is expected to extract, so harvester tests can assert against it

#### Scenario: fixtures-regeneration-deterministic
- **GIVEN** `scripts/generate_fixtures.py`
- **WHEN** it is run twice against a clean output directory
- **THEN** the two runs produce byte-identical file trees
