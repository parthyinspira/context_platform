# Tasks

- [x] 1. Add optional `source_id`, `harvested_at`, `ontology_version` fields to `Entity` and `Edge` in `harvesters/base.py` (scenarios: entity-and-edge-carry-optional-provenance-fields, entity-and-edge-default-provenance-fields-to-none) - test first
- [x] 2. `harvest_validation/report.py`: `CheckResult` and `ValidationReport` dataclasses with `to_dict()` (scenario: report-aggregates-worst-status-across-checks) - test first
- [x] 3. `harvest_validation/validator.py`: completeness check + named thresholds (scenarios: completeness-ratio-below-fail-threshold-fails, completeness-ratio-in-warn-band-warns, completeness-full-coverage-passes) - test first
- [x] 4. Exclusion integrity check (scenario: excluded type fetched) - test first
- [x] 5. Budget compliance check (scenarios: budget-exceeded-warns-and-notes-partial, budget-within-limits-passes) - test first
- [x] 6. Parse success check + named thresholds, per type (scenarios: parse-success-below-fail-threshold-fails, parse-success-in-warn-band-warns-per-type) - test first
- [x] 7. Ontology conformance check using `adapters.ontology.ENTITY_TYPES`/`RELATION_TYPES` (scenarios: unknown-entity-type-fails-ontology-conformance, missing-required-field-fails-ontology-conformance, edge-with-unknown-relation-fails-ontology-conformance) - test first
- [x] 8. Referential integrity check (scenarios: dangling-edge-warns-referential-integrity, resolved-edge-passes-referential-integrity) - test first
- [x] 9. Freshness check (scenario: cursor-not-advanced-warns-freshness) - test first
- [x] 10. `validate(...)` aggregator combining all seven checks into one `ValidationReport`, worst status wins (scenario: report-aggregates-worst-status-across-checks) - test first
- [x] 11. `harvest_validation/__init__.py` exports updated
- [x] 12. Lint (`ruff check harvesters harvest_validation`) and full test suite green
- [x] 13. Docs and contracts updated (none beyond the spec deltas; `docs/HARVESTERS.md` and `CLAUDE.md` already describe these checks and fields)
- [x] 14. verification.md completed
