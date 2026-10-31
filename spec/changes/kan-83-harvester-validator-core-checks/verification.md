# Verification

Status: PASS
Date: 2026-10-31   Commit: 20e5d21 (working tree, pre-commit for this change)

## Checks
| Check | Result |
|---|---|
| Lint (`ruff check harvesters harvest_validation --config pyproject.toml`) | PASS |
| Tests (`python -m pytest harvest_validation harvesters -q`) | PASS — 123 passed |
| Tests (full suite: `harvest_validation harvesters adapters ontology`) | PASS — 171 passed |
| `docker compose up` exercised | NOT VERIFIED — no new service/container; pure Python library code with no runtime or compose wiring. See "Not verified". |
| contract-check skill | PASS — no schema/ontology/interface/adapter mismatches; see below |
| secret-scan skill | PASS — no secrets found; only `.env.example` tracked |
| Definition of Done | PASS — tests first, scope held, docs/contracts not touched beyond spec deltas |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Standard checks / excluded type fetched | `test_exclusion_integrity_fails_when_excluded_path_fetched`, `test_exclusion_integrity_passes_when_no_excluded_path_fetched` | PASS |
| Standard checks / completeness ratio below fail threshold fails | `test_completeness_fails_below_fail_threshold` | PASS |
| Standard checks / completeness ratio in warn band warns | `test_completeness_warns_in_the_warn_band` | PASS |
| Standard checks / completeness full coverage passes | `test_completeness_passes_when_every_object_is_fetched`, `test_completeness_passes_for_empty_manifest` | PASS |
| Standard checks / budget exceeded warns and notes partial | `test_budget_compliance_warns_when_file_budget_exceeded`, `..._byte_budget_exceeded`, `..._time_budget_exceeded`, `..._token_budget_exceeded` | PASS |
| Standard checks / budget within limits passes | `test_budget_compliance_passes_within_limits`, `test_budget_compliance_passes_with_unset_budgets` | PASS |
| Standard checks / parse success below fail threshold fails | `test_parse_success_fails_below_fail_threshold_for_type` | PASS |
| Standard checks / parse success in warn band warns per type | `test_parse_success_warns_in_warn_band_for_affected_type_only` | PASS |
| Standard checks / unknown entity type fails ontology conformance | `test_ontology_conformance_fails_for_unknown_entity_type` | PASS |
| Standard checks / missing required field fails ontology conformance | `test_ontology_conformance_fails_for_missing_required_field`, `..._missing_harvested_at`, `..._missing_ontology_version` | PASS |
| Standard checks / edge with unknown relation fails ontology conformance | `test_ontology_conformance_fails_for_edge_with_unknown_relation`, `..._edge_missing_provenance` | PASS |
| Standard checks / dangling edge warns referential integrity | `test_referential_integrity_warns_for_dangling_edge` | PASS |
| Standard checks / resolved edge passes referential integrity | `test_referential_integrity_passes_when_edges_resolve`, `test_referential_integrity_accepts_previously_known_entities` | PASS |
| Standard checks / cursor not advanced warns freshness | `test_freshness_warns_when_cursor_not_advanced`, `test_freshness_warns_when_no_entity_has_harvested_at` | PASS |
| Standard checks / report aggregates worst status across checks | `test_validate_aggregates_worst_status_across_checks`, `test_validate_passes_for_a_clean_run`, `harvest_validation/tests/test_report.py` (9 tests) | PASS |
| harvester-framework / entity-and-edge-carry-optional-provenance-fields | `test_entity_and_edge_carry_optional_provenance_fields` | PASS |
| harvester-framework / entity-and-edge-default-provenance-fields-to-none | `test_entity_and_edge_default_provenance_fields_to_none` | PASS |
| harvester-framework / base-class-contract, cannot-instantiate-incomplete-subclass, registry-lookup-by-type, unknown-type-raises, duplicate-registration-rejected | `harvesters/tests/test_base.py`, `test_registry.py` (unchanged, still passing) | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Completeness | completeness-ratio-below-fail-threshold-fails, completeness-ratio-in-warn-band-warns, completeness-full-coverage-passes | PASS |
| Exclusion integrity | excluded type fetched | PASS |
| Budget compliance | budget-exceeded-warns-and-notes-partial, budget-within-limits-passes | PASS |
| Parse success | parse-success-below-fail-threshold-fails, parse-success-in-warn-band-warns-per-type | PASS |
| Ontology conformance | unknown-entity-type-fails, missing-required-field-fails, edge-unknown-relation-fails | PASS |
| Referential integrity | dangling-edge-warns, resolved-edge-passes | PASS |
| Freshness | cursor-not-advanced-warns | PASS |
| Produces ValidationReport | report-aggregates-worst-status-across-checks | PASS |

## Not verified
- End-to-end run through a real `Harvester.harvest()`/`normalize()` → `validate()` path: no concrete harvester (e.g. Git) exists yet in this repo (later story in this epic). Verified at the unit level with hand-built `Manifest`/`Entity`/`Edge` fixtures matching the real types.
- `docker compose up`: this change adds no new service, container, or compose wiring — it is pure Python library code under `harvest_validation/` and `harvesters/`, exercised by its test suite instead.
- Wiring `validate()`'s output into `PublishQuarantineGate.evaluate()` end to end: both exist and the `status` types are compatible (`harvest_validation.gate.ValidationStatus`), but no orchestrator calls both in sequence yet (out of scope, no `harvest_runs` persistence/dispatcher exists).
