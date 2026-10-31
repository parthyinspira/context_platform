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
