# Delta for harvester framework

## MODIFIED Requirements
### Requirement: Lifecycle
A harvester SHALL implement connect, discover, profile, plan, harvest, normalize and validate, and each run SHALL record its state in `harvest_runs`. (was: stated the requirement with no `harvesters` package, interface or `harvest_runs` table in code)

#### Scenario: full run
- **Given** an approved plan
- **When** a run executes
- **Then** states progress CONNECTING to PUBLISHED or QUARANTINED, each recorded

#### Scenario: harvester-interface-has-all-stages
- **Given** the `harvesters.base.Harvester` abstract base class (extended in place by this story; see "Base class and plugin registry" requirement)
- **When** its abstract methods are inspected
- **Then** it declares `connect`, `discover`, `profile`, `plan`, `harvest`, `normalize` and `validate`

#### Scenario: abstract-class-cannot-skip-a-method
- **Given** a subclass of `Harvester` that omits one of the seven methods
- **When** it is instantiated
- **Then** Python raises `TypeError` for the missing abstract method

#### Scenario: harvest-runs-table-created
- **Given** migration `0004_harvest_runs` applied to an empty database
- **When** the schema is inspected
- **Then** a `harvest_runs` table exists with `id`, `source_id`, `state`, `plan`, `manifest`, `error`, `started_at`, `updated_at` columns

#### Scenario: harvest-runs-accepts-valid-states
- **Given** the `harvest_runs` table
- **When** a row is inserted for each of `CONNECTING, DISCOVERING, PROFILING, PLANNED, APPROVED, HARVESTING, VALIDATING, PUBLISHED, QUARANTINED, FAILED, PARTIAL`
- **Then** every insert succeeds

#### Scenario: harvest-runs-rejects-invalid-state
- **Given** the `harvest_runs` table
- **When** a row is inserted with `state = 'BOGUS'`
- **Then** the insert is rejected by the `CHECK` constraint

#### Scenario: migration-up-creates-table
- **Given** an empty database
- **When** `scripts/migrate.py up` runs
- **Then** `harvest_runs` exists and is recorded in `schema_migrations`

#### Scenario: migration-down-drops-table
- **Given** migration `0004_harvest_runs` applied
- **When** `scripts/migrate.py down` runs
- **Then** `harvest_runs` no longer exists

#### Scenario: migration-reapply-is-no-op
- **Given** migration `0004_harvest_runs` already applied
- **When** `scripts/migrate.py up` runs again
- **Then** no error occurs and `schema_migrations` is unchanged

### Requirement: Base class and plugin registry
The project SHALL provide an abstract `Harvester` base class implementing the full lifecycle from `docs/HARVESTERS.md` section 2 — `connect`, `discover` (returning `ScopeTree`), `profile`, `plan` (returning the shared `harvesters.framework.HarvestPlan`), `harvest` (replacing `fetch`, plan-driven and bulk), `normalize` and `validate` — extending the original `discover`/`fetch`/`normalize` contract added by KAN-12. (was: base class implemented only `discover(source) -> Iterable[ObjectRef]`, `fetch(source, ref, cursor) -> RawObject` and `normalize(raw) -> list[Entity | Edge | Chunk]`)

#### Scenario: base-class-contract
- **Given** a subclass of `Harvester` that implements all seven lifecycle methods
- **When** it is instantiated and its methods are called
- **Then** it satisfies the `Harvester` interface and returns the documented types

#### Scenario: cannot-instantiate-incomplete-subclass
- **Given** a subclass of `Harvester` that omits one of the seven lifecycle methods
- **When** it is instantiated
- **Then** instantiation raises `TypeError` because the abstract method is not implemented
