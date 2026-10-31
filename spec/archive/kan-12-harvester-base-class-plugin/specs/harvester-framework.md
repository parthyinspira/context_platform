# Delta for harvester-framework

## ADDED Requirements
### Requirement: Base class and plugin registry
The project SHALL provide an abstract `Harvester` base class implementing the `discover(source) -> Iterable[ObjectRef]`, `fetch(source, ref, cursor) -> RawObject` and `normalize(raw) -> list[Entity | Edge | Chunk]` interface from `CLAUDE.md`, and a plugin registry SHALL select the concrete `Harvester` implementation for a source by its `source.type`.

#### Scenario: base-class-contract
- **Given** a subclass of `Harvester` that implements `discover`, `fetch` and `normalize`
- **When** it is instantiated and its methods are called
- **Then** it satisfies the `Harvester` interface and returns the documented types

#### Scenario: cannot-instantiate-incomplete-subclass
- **Given** a subclass of `Harvester` that omits one of `discover`, `fetch` or `normalize`
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
