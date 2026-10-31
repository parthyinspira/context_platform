# KAN-12: Harvester base class and plugin registry

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-12   Epic: 3 Git harvester end to end   Branch: kan-12-harvester-base-class-plugin

## Why
Epic 3 needs a concrete Git harvester, but nothing in the repo yet defines the harvester interface from `CLAUDE.md` in code, nor a way to pick a harvester implementation for a given `sources.type`. This story adds that shared foundation (base class + plugin registry) so KAN-13+ can add the Git harvester itself by registering against it, and later source types register the same way without touching dispatcher code.

## What changes
- Add `harvesters/base.py` defining the abstract `Harvester` interface from `CLAUDE.md`: `discover(source) -> Iterable[ObjectRef]`, `fetch(source, ref, cursor) -> RawObject`, `normalize(raw) -> list[Entity | Edge | Chunk]`, plus the small value types (`ObjectRef`, `RawObject`) and the `Entity`/`Edge`/`Chunk` normalize-output types shared with the Postgres schema v0.
- Add `harvesters/registry.py`: a plugin registry mapping `source.type` -> `Harvester` subclass, with a `@register_harvester("type")` decorator and `get_harvester(source_type) -> Harvester` lookup that raises a clear error for an unregistered type.
- Add `harvesters/__init__.py` importing registered harvester modules so registration happens on package import (mirrors the pattern in `adapters/factory.py` for adapter selection by `.env` key, but keyed by `source.type` instead).
- No concrete source-type harvester ships in this story (Git, SQL, SharePoint, etc. are later stories per `docs/HARVESTERS.md` section 6 and the Build order in `CLAUDE.md`); tests use two small fixture harvester classes registered under fake types to prove discover/fetch/normalize and registry selection work end to end.

## In scope
- Abstract `Harvester` base class with `discover`/`fetch`/`normalize` exactly as specified in `CLAUDE.md`'s harvester interface contract.
- `ObjectRef`, `RawObject` value types passed between the three methods, and reuse of `Entity`/`Edge`/`Chunk` shapes consistent with the Postgres schema v0 (`entities`, `edges`, `chunks` columns: `source_id`, `external_id`, `harvested_at`, etc.).
- A plugin registry keyed by `source.type` string, with explicit registration (no filesystem/dynamic plugin discovery magic) and a clear `UnknownSourceTypeError` for an unregistered type.
- Unit tests for the base class contract (cannot instantiate directly; subclass must implement all three methods) and the registry (register, duplicate-register behavior, lookup, unknown-type error).

## Out of scope
- The full `connect/discover/profile/plan/harvest/validate` lifecycle and `harvest_runs` state machine from `docs/HARVESTERS.md` / `spec/capabilities/harvester-framework.md` — that capability already exists as a spec for later stories (dispatcher, validator, budgets) and is not re-scoped here; this story only implements the three-method contract named in this AC (`discover/fetch/normalize`) plus plugin selection.
- A concrete Git, SQL, SharePoint or Tableau harvester (later stories: KAN-13+ per the Build order in `CLAUDE.md`).
- Wiring the registry into the scheduler/dispatcher container (Epic 4); this story only provides the registry module itself.
- Incremental cursor logic, budgets, secret scanning, validation reports — all named in `docs/HARVESTERS.md` but tied to a real harvester implementation, not the base class.

## Acceptance criteria (from Jira)
1. discover/fetch/normalize interface implemented -> scenarios: base-class-contract, cannot-instantiate-incomplete-subclass
2. harvester chosen by source.type -> scenarios: registry-lookup-by-type, unknown-type-raises, duplicate-registration-rejected

## Affected
Capabilities: `spec/capabilities/harvester-framework.md` (new requirement: base class + plugin registry, scoped to discover/fetch/normalize)   Docs/contracts: none (no schema/ontology change; the harvester interface itself is unchanged from `CLAUDE.md`, now implemented in code) — no Confluence Contracts update needed since the interface text is not changing, only being implemented.

## Risks and open questions
- `spec/capabilities/harvester-framework.md` already specifies a 7-method lifecycle (`connect/discover/profile/plan/harvest/normalize/validate`) for a fully built harvester. This story deliberately implements only the 3-method contract named in the KAN-12 AC and in `CLAUDE.md`'s "Harvester interface" section, as a base that a later story can extend to the full lifecycle. Flagged here rather than silently narrowing scope.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
