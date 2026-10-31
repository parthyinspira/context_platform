# Delta for postgres schema

## ADDED Requirements

### Requirement: Schema applied by repeatable migrations
The system SHALL create `sources`, `entities`, `edges`, `chunks` and `proposed_changes` only through forward SQL migrations tracked in a migration-history table; schema SHALL NOT be created or changed by hand.
#### Scenario: fresh database
- **Given** an empty Postgres database with the `vector` extension available
- **When** the migrations are applied in order
- **Then** all five tables exist with the columns named in CLAUDE.md's "Postgres schema v0" section, and the migration-history table records each applied migration

#### Scenario: idempotent re-run
- **Given** a database where all migrations have already been applied
- **When** the migration runner is run again
- **Then** no migration is re-applied and no error occurs

#### Scenario: rollback
- **Given** a database with the v0 migrations applied
- **When** the down migration(s) are run
- **Then** the five tables are dropped and the migration-history table no longer lists them as applied

### Requirement: Schema matches the contract
The columns, types and constraints created by the migrations SHALL match the "Postgres schema v0" section of CLAUDE.md and the Confluence Contracts page.
#### Scenario: columns match contract
- **Given** the applied schema
- **When** each table's columns are compared to CLAUDE.md's "Postgres schema v0" list
- **Then** every listed column is present with a compatible type, including `tombstoned_at` on `entities`, `embedding_model` on `chunks`, and `ontology_version` on `entities` and `edges`

#### Scenario: Confluence updated
- **Given** the migrations are merged
- **When** the Confluence Contracts page is checked
- **Then** it lists the same tables and columns as the migrations
