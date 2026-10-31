# KAN-83: Harvester validator core checks

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-83   Epic: 10 Harvester framework - planning, scoping, validation   Branch: kepler/kan-83-harvester-validator-core-checks

## Why
`docs/HARVESTERS.md` section 5 and `spec/capabilities/harvest-validation.md` describe a validator with ten checks producing a `PASS | WARN | FAIL` report, but only the publish/quarantine gate (`harvest_validation/gate.py`, KAN-85) exists today — it consumes a status, it does not produce one. No code implements any of the checks themselves. This story builds the first seven: completeness, exclusion integrity, budget compliance, parse success, ontology conformance, referential integrity and freshness, and the `ValidationReport` structure they populate, so a future harvester can call `validate()` and feed the result straight into the existing gate.

## What changes
- New `harvest_validation/report.py`: `CheckResult` (name, status, message, counts, sample failures) and `ValidationReport` (overall `status: ValidationStatus`, tuple of `CheckResult`), with a `to_dict()` for the UI report view.
- New `harvest_validation/validator.py`: named threshold constants and one function per check (`check_completeness`, `check_exclusion_integrity`, `check_budget_compliance`, `check_parse_success`, `check_ontology_conformance`, `check_referential_integrity`, `check_freshness`), plus `validate(...)` that runs all seven and aggregates the worst status (FAIL > WARN > PASS) into one `ValidationReport`. Consumes the real `harvesters.framework.manifest.Manifest` (`by_outcome()`, `counts()`, `unaccounted()`), `harvesters.framework.plan.HarvestPlan`, and `harvesters.base.Entity`/`Edge` — no parallel types.
- Small additive change to `harvesters/base.py`: `Entity` and `Edge` gain optional `source_id: str | None`, `harvested_at: datetime | None`, `ontology_version: str | None` fields (default `None`), needed so ontology-conformance and freshness can check their presence per `CLAUDE.md`'s "every record carries `source_id` and `harvested_at`" and "every fact stores `ontology_version`, `source_id`, `confidence`". Existing construction call sites (tests, fixtures) are unaffected since the fields are optional and default to `None`.
- Ontology conformance validates emitted types against `adapters.ontology.ENTITY_TYPES` / `RELATION_TYPES` (the single source of truth), not a hardcoded list.
- Report structure satisfies the existing "Report" requirement's "view report" scenario (every check shows result and counts); that requirement's text is not duplicated in the delta below.
- Unit tests under `harvest_validation/tests/test_validator.py` covering PASS/WARN/FAIL per check and combined.

## In scope
- The seven checks named in the Jira AC and their thresholds, as named constants.
- The `ValidationReport`/`CheckResult` structures and the `validate()` aggregator.
- The minimal `Entity`/`Edge` field additions needed to check ontology conformance and freshness.
- Unit tests for each check and for aggregation (worst-of wins).

## Out of scope
- Expected yield, secrets/PII, and spot-check checks (not in the Jira AC).
- Delete sanity and the PASS/WARN/FAIL publish/quarantine gate (`harvest_validation/gate.py`) — already implemented (KAN-85); this story only produces a report whose `status` the gate can consume.
- Wiring `validate()` into a concrete harvester's `Harvester.validate()` override, the dispatcher, or the UI report view — no concrete harvester exists yet (Git harvester is a later story in this epic).
- Any change to the Postgres schema or migrations — `source_id`/`ontology_version`/`harvested_at` already exist as columns in `entities`/`edges` (`CLAUDE.md` schema v0); this only adds matching fields to the in-memory dataclasses that are normalize()'s output, before a write path exists.

## Acceptance criteria (from Jira)
"AC: completeness, exclusion integrity, budget compliance, parse success, ontology conformance, referential integrity, freshness; produces ValidationReport."
1. Completeness -> scenario: completeness-ratio-below-fail-threshold-fails, completeness-ratio-in-warn-band-warns, completeness-full-coverage-passes
2. Exclusion integrity -> scenario: excluded-path-fetched-fails (already covered by the existing scenario in `spec/capabilities/harvest-validation.md`; kept, not duplicated)
3. Budget compliance -> scenario: budget-exceeded-warns-partial, budget-within-limits-passes
4. Parse success -> scenario: parse-success-below-fail-threshold-fails, parse-success-in-warn-band-warns-per-type
5. Ontology conformance -> scenario: unknown-entity-type-fails, missing-required-field-fails, edge-unknown-relation-fails
6. Referential integrity -> scenario: dangling-edge-warns
7. Freshness -> scenario: cursor-not-advanced-warns
- "produces ValidationReport" -> scenario: report-aggregates-worst-status-across-checks (all of the above feed this)

## Affected
Capabilities: `spec/capabilities/harvest-validation.md` (modified — adds scenarios to "Standard checks"), `spec/capabilities/harvester-framework.md` (modified — documents the new optional `Entity`/`Edge` fields).   Docs/contracts: none beyond what's already in `docs/HARVESTERS.md` section 5 and `CLAUDE.md`'s Postgres schema v0 (no new contract introduced; `source_id`/`ontology_version`/`harvested_at` were already documented columns, just not yet reflected on the in-memory types).

## Risks and open questions
- No concrete harvester exists yet to call `validate()` end to end, so this story is tested at the unit level against hand-built `Manifest`/`Entity`/`Edge` fixtures, not a real harvest run. Flagged under "Not verified" at verification time.
- Thresholds (completeness, parse-success ratios) are chosen as reasonable defaults per `docs/HARVESTERS.md`'s "above a threshold" language, since Jira does not specify exact numbers; documented as named constants so a later story can tune them without code changes elsewhere.
- Budget compliance is checked after the fact from the manifest and optional elapsed-time/token counters (no live `BudgetTracker` wiring exists yet since no harvester runs); this only compares recorded usage to `HarvestPlan.budgets`.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR.
