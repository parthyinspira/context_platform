# Delta for harvester-framework

## MODIFIED Requirements
### Requirement: Base class and plugin registry
The project SHALL provide an abstract `Harvester` base class implementing the full lifecycle from `docs/HARVESTERS.md` section 2 — `connect(source) -> ConnectionResult`, `discover(source) -> ScopeTree`, `profile(source, scope) -> Profile`, `plan(profile) -> HarvestPlan` (the shared `HarvestPlan` model, not a per-harvester type), `harvest(source, plan, cursor) -> Iterable[RawObject]`, `normalize(raw) -> list[Entity | Edge | Chunk]` and `validate(plan, manifest) -> ValidationReport` — extending the original `discover`/`fetch`/`normalize` contract in `CLAUDE.md` (KAN-75). A plugin registry SHALL select the concrete `Harvester` implementation for a source by its `source.type`. `Entity` and `Edge` SHALL each carry optional `source_id`, `harvested_at` and `ontology_version` fields (default `None`) so a validator can check their presence before a harvest is published, matching the `source_id`/`ontology_version`/`harvested_at` columns already documented on `entities`/`edges` in `CLAUDE.md`'s Postgres schema v0. (was: `Entity` held only `type`, `name`, `external_id`, `props`; `Edge` held only `src_external_id`, `dst_external_id`, `relation`, `confidence` — neither carried the provenance fields the validator (KAN-83) needs to check.)

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

#### Scenario: entity-and-edge-carry-optional-provenance-fields
- **Given** an `Entity` and an `Edge` constructed with `source_id`, `harvested_at` and `ontology_version` set
- **When** their fields are read
- **Then** each value is present exactly as set

#### Scenario: entity-and-edge-default-provenance-fields-to-none
- **Given** an `Entity` and an `Edge` constructed the way existing call sites already do, without the new fields
- **When** they are built
- **Then** construction succeeds and `source_id`, `harvested_at` and `ontology_version` are each `None`
