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

### Requirement: Harvest plan model
A `HarvestPlan` SHALL hold include/exclude rules, a per-object size cap and budgets for files, bytes, wall time and tokens; exclude rules SHALL take precedence over include rules.

#### Scenario: include-exclude-precedence
- **Given** a plan with include pattern `*.sql` and exclude pattern `*/target/*`
- **When** a path matching both is checked
- **Then** the path is excluded

#### Scenario: plan-holds-caps-and-budgets
- **Given** a plan built with a size cap and budgets for files, bytes, time and tokens
- **When** the plan is read
- **Then** each value is present on the plan exactly as set

#### Scenario: default-plan-is-unrestricted
- **Given** a plan built with no arguments
- **When** a path is checked and the budgets are read
- **Then** the path is included and every budget dimension is unset (unlimited)

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
A harvester SHALL use read-only credentials and SHALL redact detected secrets before storage, using the shared scanner (`adapters.scanning.scan_and_redact`), which also detects common PII and derives a `sensitivity` level.

#### Scenario: secret in a file
- **Given** a file containing an API key
- **When** it is harvested
- **Then** the key is redacted in stored text and the object is marked sensitive

#### Scenario: AWS key, token, password, private key detected
- **Given** text containing a seeded AWS-shaped access key, a generic API token, a password assignment, and a PEM private key block
- **When** the text is scanned
- **Then** each is detected and replaced with a redaction marker in the returned text, and none of the original secret values appear in the output

#### Scenario: PII detected without a secret
- **Given** text containing only an email address or an SSN-shaped number, with no secret pattern present
- **When** the text is scanned
- **Then** the PII is redacted and the derived sensitivity is `confidential`, not `restricted`

#### Scenario: no findings
- **Given** text containing no secret or PII pattern
- **When** the text is scanned
- **Then** the text is returned unchanged and the derived sensitivity is `internal`

#### Scenario: redaction before storage
- **Given** text containing a seeded secret
- **When** `PostgresChunkWriter.write()` is called with that text
- **Then** the row inserted into `chunks.text` contains the redaction marker, never the raw secret value, and `chunks.metadata` records `sensitivity: "restricted"`

### Requirement: Idempotent incremental runs
Re-running a harvest SHALL NOT create duplicates and SHALL only process changes since the cursor.
#### Scenario: rerun unchanged
- **Given** a completed harvest
- **When** it is run again with no source changes
- **Then** no entities are created or changed

### Requirement: Base class and plugin registry
The project SHALL provide an abstract `Harvester` base class implementing the full lifecycle from `docs/HARVESTERS.md` section 2 — `connect(source) -> ConnectionResult`, `discover(source) -> ScopeTree`, `profile(source, scope) -> Profile`, `plan(profile) -> HarvestPlan` (the shared `HarvestPlan` model, not a per-harvester type), `harvest(source, plan, cursor) -> Iterable[RawObject]`, `normalize(raw) -> list[Entity | Edge | Chunk]` and `validate(plan, manifest) -> ValidationReport` — extending the original `discover`/`fetch`/`normalize` contract in `CLAUDE.md` (KAN-75). A plugin registry SHALL select the concrete `Harvester` implementation for a source by its `source.type`.

#### Scenario: base-class-contract
- **Given** a subclass of `Harvester` that implements all seven lifecycle methods
- **When** it is instantiated and its methods are called
- **Then** it satisfies the `Harvester` interface and returns the documented types

#### Scenario: cannot-instantiate-incomplete-subclass
- **Given** a subclass of `Harvester` that omits one of the seven lifecycle methods
- **When** it is instantiated
- **Then** instantiation raises `TypeError` because the abstract method is not implemented

#### Scenario: registry-lookup-by-type
- **Given** a `Harvester` subclass registered for source type `"git"`
- **When** `get_harvester("git")` is called
- **Then** it returns an instance of that subclass

#### Scenario: unknown-type-raises
- **Given** no harvester registered for source type `"unknown-type"`
- **When** `get_harvester("unknown-type")` is called
- **Then** it raises `UnknownSourceTypeError` naming the unregistered type

#### Scenario: duplicate-registration-rejected
- **Given** a harvester already registered for source type `"git"`
- **When** a second, different `Harvester` subclass is registered for `"git"`
- **Then** registration raises a clear error instead of silently overwriting the first

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
