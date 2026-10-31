"""Tests for the harvester validator checks (KAN-83, KAN-84).

The KAN-83 tests (completeness, exclusion integrity, budget compliance, parse
success, ontology conformance, referential integrity, freshness, `validate`)
map to
spec/changes/kan-83-harvester-validator-core-checks/specs/harvest-validation.md.
The KAN-84 tests (expected yield, delete sanity, secrets/PII, `run_checks`)
were already merged to `main` before this file existed on this branch; they
are combined here because both stories added `harvest_validation/
validator.py` independently.
"""
from datetime import UTC, datetime

from harvest_validation.gate import ValidationStatus
from harvest_validation.validator import (
    CheckStatus,
    check_budget_compliance,
    check_completeness,
    check_delete_sanity,
    check_exclusion_integrity,
    check_expected_yield,
    check_freshness,
    check_ontology_conformance,
    check_parse_success,
    check_referential_integrity,
    check_secrets_and_pii,
    run_checks,
    validate,
)
from harvesters.base import Edge, Entity
from harvesters.base import ValidationReport as HarvesterValidationReport
from harvesters.framework.manifest import Manifest
from harvesters.framework.plan import Budgets, HarvestPlan

SOURCE_ID = "11111111-1111-1111-1111-111111111111"
RUN_ID = "run-0001"
FIXED_NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


def _manifest() -> Manifest:
    return Manifest(source_id=SOURCE_ID, run_id=RUN_ID, now=lambda: FIXED_NOW)


def _entity(external_id: str = "orders", **overrides) -> Entity:
    defaults = dict(
        type="Table",
        name=external_id,
        external_id=external_id,
        source_id=SOURCE_ID,
        harvested_at=FIXED_NOW,
        ontology_version="v0",
    )
    defaults.update(overrides)
    return Entity(**defaults)


def _edge(src: str = "a", dst: str = "b", **overrides) -> Edge:
    defaults = dict(
        src_external_id=src,
        dst_external_id=dst,
        relation="READS_FROM",
        source_id=SOURCE_ID,
        harvested_at=FIXED_NOW,
        ontology_version="v0",
    )
    defaults.update(overrides)
    return Edge(**defaults)


# --- completeness -----------------------------------------------------------


def test_completeness_passes_when_every_object_is_fetched():
    m = _manifest()
    for i in range(10):
        m.discovered(f"f{i}.sql", reason="listed")
        m.fetched(f"f{i}.sql", reason="matched include")

    result = check_completeness(m)

    assert result.status == ValidationStatus.PASS


def test_completeness_warns_in_the_warn_band():
    m = _manifest()
    for i in range(10):
        m.discovered(f"f{i}.sql", reason="listed")
    for i in range(9):
        m.fetched(f"f{i}.sql", reason="matched include")
    m.skipped("f9.sql", reason="over size cap")

    result = check_completeness(m)

    assert result.status == ValidationStatus.WARN


def test_completeness_fails_below_fail_threshold():
    m = _manifest()
    for i in range(10):
        m.discovered(f"f{i}.sql", reason="listed")
    for i in range(5):
        m.fetched(f"f{i}.sql", reason="matched include")
    for i in range(5, 10):
        m.failed(f"f{i}.sql", reason="fetch error")

    result = check_completeness(m)

    assert result.status == ValidationStatus.FAIL


def test_completeness_passes_for_empty_manifest():
    result = check_completeness(_manifest())

    assert result.status == ValidationStatus.PASS


def test_completeness_lists_unaccounted_objects_as_samples():
    m = _manifest()
    m.discovered("pending.sql", reason="listed")

    result = check_completeness(m)

    assert "pending.sql" in result.samples


# --- exclusion integrity -----------------------------------------------------


def test_exclusion_integrity_fails_when_excluded_path_fetched():
    plan = HarvestPlan(exclude=("*/target/*",))
    m = _manifest()
    m.discovered("build/target/app.jar", reason="listed by ls-tree")
    m.fetched("build/target/app.jar", reason="fetched by mistake")

    result = check_exclusion_integrity(plan, m)

    assert result.status == ValidationStatus.FAIL
    assert "build/target/app.jar" in result.samples


def test_exclusion_integrity_passes_when_no_excluded_path_fetched():
    plan = HarvestPlan(exclude=("*/target/*",))
    m = _manifest()
    m.discovered("models/stg_orders.sql", reason="listed")
    m.fetched("models/stg_orders.sql", reason="matched include")
    m.discovered("build/target/app.jar", reason="listed")
    m.skipped("build/target/app.jar", reason="excluded: build output")

    result = check_exclusion_integrity(plan, m)

    assert result.status == ValidationStatus.PASS


# --- budget compliance --------------------------------------------------------


def test_budget_compliance_warns_when_file_budget_exceeded():
    plan = HarvestPlan(budgets=Budgets(max_files=2))
    m = _manifest()
    for i in range(3):
        m.discovered(f"f{i}.sql", reason="listed")
        m.fetched(f"f{i}.sql", reason="matched include")

    result = check_budget_compliance(plan, m)

    assert result.status == ValidationStatus.WARN
    assert "files" in result.samples
    assert "PARTIAL" in result.message


def test_budget_compliance_warns_when_byte_budget_exceeded():
    plan = HarvestPlan(budgets=Budgets(max_bytes=100))
    m = _manifest()
    m.discovered("big.sql", reason="listed", size_bytes=500)
    m.fetched("big.sql", reason="matched include")

    result = check_budget_compliance(plan, m)

    assert result.status == ValidationStatus.WARN
    assert "bytes" in result.samples


def test_budget_compliance_warns_when_time_budget_exceeded():
    plan = HarvestPlan(budgets=Budgets(max_seconds=10))
    m = _manifest()

    result = check_budget_compliance(plan, m, elapsed_seconds=20)

    assert result.status == ValidationStatus.WARN
    assert "time" in result.samples


def test_budget_compliance_warns_when_token_budget_exceeded():
    plan = HarvestPlan(budgets=Budgets(max_tokens=100))
    m = _manifest()

    result = check_budget_compliance(plan, m, tokens_used=500)

    assert result.status == ValidationStatus.WARN
    assert "tokens" in result.samples


def test_budget_compliance_passes_within_limits():
    plan = HarvestPlan(budgets=Budgets(max_files=10, max_bytes=10_000))
    m = _manifest()
    m.discovered("f.sql", reason="listed", size_bytes=100)
    m.fetched("f.sql", reason="matched include")

    result = check_budget_compliance(plan, m)

    assert result.status == ValidationStatus.PASS


def test_budget_compliance_passes_with_unset_budgets():
    plan = HarvestPlan()
    m = _manifest()
    m.discovered("f.sql", reason="listed", size_bytes=10_000_000)
    m.fetched("f.sql", reason="matched include")

    result = check_budget_compliance(plan, m)

    assert result.status == ValidationStatus.PASS


# --- parse success -------------------------------------------------------------


def test_parse_success_passes_with_no_errors():
    m = _manifest()
    for i in range(5):
        m.discovered(f"f{i}.sql", reason="listed")
        m.fetched(f"f{i}.sql", reason="matched include")

    result = check_parse_success(m, parse_errors={})

    assert result.status == ValidationStatus.PASS


def test_parse_success_warns_in_warn_band_for_affected_type_only():
    m = _manifest()
    for i in range(20):
        m.discovered(f"f{i}.sql", reason="listed")
        m.fetched(f"f{i}.sql", reason="matched include")
    m.discovered("ok.java", reason="listed")
    m.fetched("ok.java", reason="matched include")

    # 2/20 sql files fail -> ratio 0.90, inside the warn band (>=0.80, <0.95).
    result = check_parse_success(m, parse_errors={"f0.sql": "bad syntax", "f1.sql": "bad syntax"})

    assert result.status == ValidationStatus.WARN
    assert "sql" in result.message
    assert "java" not in result.message


def test_parse_success_fails_below_fail_threshold_for_type():
    m = _manifest()
    for i in range(10):
        m.discovered(f"f{i}.sql", reason="listed")
        m.fetched(f"f{i}.sql", reason="matched include")

    errors = {f"f{i}.sql": "bad syntax" for i in range(5)}
    result = check_parse_success(m, parse_errors=errors)

    assert result.status == ValidationStatus.FAIL


def test_parse_success_passes_when_nothing_fetched():
    result = check_parse_success(_manifest())

    assert result.status == ValidationStatus.PASS


# --- ontology conformance -------------------------------------------------------


def test_ontology_conformance_passes_for_well_formed_records():
    result = check_ontology_conformance([_entity()], [_edge()])

    assert result.status == ValidationStatus.PASS


def test_ontology_conformance_fails_for_unknown_entity_type():
    result = check_ontology_conformance([_entity(type="NotAType")], [])

    assert result.status == ValidationStatus.FAIL
    assert "NotAType" in result.samples[0]


def test_ontology_conformance_fails_for_missing_required_field():
    result = check_ontology_conformance([_entity(source_id=None)], [])

    assert result.status == ValidationStatus.FAIL
    assert "source_id" in result.samples[0]


def test_ontology_conformance_fails_for_missing_harvested_at():
    result = check_ontology_conformance([_entity(harvested_at=None)], [])

    assert result.status == ValidationStatus.FAIL
    assert "harvested_at" in result.samples[0]


def test_ontology_conformance_fails_for_missing_ontology_version():
    result = check_ontology_conformance([_entity(ontology_version=None)], [])

    assert result.status == ValidationStatus.FAIL
    assert "ontology_version" in result.samples[0]


def test_ontology_conformance_fails_for_edge_with_unknown_relation():
    result = check_ontology_conformance([], [_edge(relation="FRIENDS_WITH")])

    assert result.status == ValidationStatus.FAIL
    assert "FRIENDS_WITH" in result.samples[0]


def test_ontology_conformance_fails_for_edge_missing_provenance():
    result = check_ontology_conformance([], [_edge(source_id=None, ontology_version=None)])

    assert result.status == ValidationStatus.FAIL


# --- referential integrity -------------------------------------------------------


def test_referential_integrity_passes_when_edges_resolve():
    entities = [_entity("a"), _entity("b")]
    edges = [_edge("a", "b")]

    result = check_referential_integrity(entities, edges)

    assert result.status == ValidationStatus.PASS


def test_referential_integrity_warns_for_dangling_edge():
    entities = [_entity("a")]
    edges = [_edge("a", "missing")]

    result = check_referential_integrity(entities, edges)

    assert result.status == ValidationStatus.WARN
    assert any("missing" in s for s in result.samples)


def test_referential_integrity_accepts_previously_known_entities():
    entities = [_entity("a")]
    edges = [_edge("a", "already-published")]

    result = check_referential_integrity(
        entities, edges, known_external_ids=["already-published"]
    )

    assert result.status == ValidationStatus.PASS


# --- freshness -------------------------------------------------------------------


def test_freshness_passes_when_cursor_advanced_and_harvested_at_set():
    result = check_freshness(cursor_advanced=True, entities=[_entity()])

    assert result.status == ValidationStatus.PASS


def test_freshness_warns_when_cursor_not_advanced():
    result = check_freshness(cursor_advanced=False, entities=[_entity()])

    assert result.status == ValidationStatus.WARN
    assert "cursor" in result.message


def test_freshness_warns_when_no_entity_has_harvested_at():
    result = check_freshness(
        cursor_advanced=True, entities=[_entity(harvested_at=None), _entity("b", harvested_at=None)]
    )

    assert result.status == ValidationStatus.WARN


def test_freshness_passes_with_no_entities_and_advanced_cursor():
    result = check_freshness(cursor_advanced=True, entities=[])

    assert result.status == ValidationStatus.PASS


# --- validate() aggregation --------------------------------------------------------


def test_validate_aggregates_worst_status_across_checks():
    plan = HarvestPlan()
    m = _manifest()
    m.discovered("orders.sql", reason="listed")
    m.fetched("orders.sql", reason="matched include")

    entities = [_entity("orders")]
    edges = [_edge("orders", "missing", relation="BOGUS_RELATION")]

    report = validate(plan, m, entities, edges, cursor_advanced=True)

    assert report.status == ValidationStatus.FAIL
    assert report.check("ontology_conformance").status == ValidationStatus.FAIL
    assert report.check("referential_integrity").status == ValidationStatus.WARN
    assert report.check("completeness").status == ValidationStatus.PASS
    assert {c.name for c in report.checks} == {
        "completeness",
        "exclusion_integrity",
        "budget_compliance",
        "parse_success",
        "ontology_conformance",
        "referential_integrity",
        "freshness",
    }


def test_validate_passes_for_a_clean_run():
    plan = HarvestPlan(exclude=("*/target/*",))
    m = _manifest()
    m.discovered("orders.sql", reason="listed")
    m.fetched("orders.sql", reason="matched include")

    entities = [_entity("orders")]
    edges = [_edge("orders", "orders")]

    report = validate(plan, m, entities, edges, cursor_advanced=True)

    assert report.status == ValidationStatus.PASS


# -- check_expected_yield -----------------------------------------------------


def test_zero_yield_fails() -> None:
    result = check_expected_yield(detected_stacks=["sql_dbt"], counts_by_type={})

    assert result.status == CheckStatus.FAIL
    assert "zero" in result.detail.lower()


def test_stack_missing_expected_entities_fails() -> None:
    result = check_expected_yield(
        detected_stacks=["sql_dbt", "talend"],
        counts_by_type={"Job": 3},
    )

    assert result.status == CheckStatus.FAIL
    assert "sql_dbt" in result.detail
    assert "talend" not in result.detail


def test_expected_yield_passes() -> None:
    result = check_expected_yield(
        detected_stacks=["sql_dbt", "talend"],
        counts_by_type={"Table": 5, "Job": 3},
    )

    assert result.status == CheckStatus.PASS


def test_expected_yield_skips_unknown_stacks() -> None:
    result = check_expected_yield(
        detected_stacks=["sql_dbt", "mystery_stack"],
        counts_by_type={"Table": 1},
    )

    assert result.status == CheckStatus.PASS


# -- check_delete_sanity -------------------------------------------------------


def test_delete_spike_fails() -> None:
    result = check_delete_sanity(tombstoned_count=40, previously_published_count=100)

    assert result.status == CheckStatus.FAIL
    assert "delete" in result.detail.lower() or "tombstone" in result.detail.lower()


def test_delete_below_threshold_passes() -> None:
    result = check_delete_sanity(tombstoned_count=10, previously_published_count=100)

    assert result.status == CheckStatus.PASS


def test_delete_exactly_at_threshold_passes() -> None:
    result = check_delete_sanity(tombstoned_count=20, previously_published_count=100, threshold=0.2)

    assert result.status == CheckStatus.PASS


def test_delete_sanity_passes_with_nothing_previously_published() -> None:
    result = check_delete_sanity(tombstoned_count=5, previously_published_count=0)

    assert result.status == CheckStatus.PASS


def test_delete_sanity_custom_threshold() -> None:
    result = check_delete_sanity(tombstoned_count=15, previously_published_count=100, threshold=0.1)

    assert result.status == CheckStatus.FAIL


# -- check_secrets_and_pii -----------------------------------------------------


def test_unredacted_secret_fails() -> None:
    result = check_secrets_and_pii(
        {
            "repo-a/config.yml": "api_key: abcdef0123456789",
            "repo-a/readme.md": "nothing sensitive here",
        }
    )

    assert result.status == CheckStatus.FAIL
    assert "repo-a/config.yml" in result.detail
    assert "repo-a/readme.md" not in result.detail


def test_redacted_content_passes() -> None:
    result = check_secrets_and_pii(
        {
            "repo-a/config.yml": "api_key: [REDACTED:generic_api_key]",
            "repo-a/readme.md": "nothing sensitive here",
        }
    )

    assert result.status == CheckStatus.PASS


def test_secrets_check_passes_on_empty_input() -> None:
    result = check_secrets_and_pii({})

    assert result.status == CheckStatus.PASS


# -- run_checks -----------------------------------------------------------------


def test_run_checks_all_pass_yields_pass_report() -> None:
    report = run_checks(
        detected_stacks=["sql_dbt"],
        counts_by_type={"Table": 2},
        tombstoned_count=1,
        previously_published_count=100,
        stored_texts={"repo-a/models/x.sql": "select 1"},
    )

    assert isinstance(report, HarvesterValidationReport)
    assert report.status == "PASS"
    assert report.checks["expected_yield"] == "PASS"
    assert report.checks["delete_sanity"] == "PASS"
    assert report.checks["secrets_and_pii"] == "PASS"
    assert report.errors == []


def test_run_checks_any_fail_yields_fail_report_with_errors() -> None:
    report = run_checks(
        detected_stacks=["sql_dbt"],
        counts_by_type={},
        tombstoned_count=40,
        previously_published_count=100,
        stored_texts={"repo-a/config.yml": "password: hunter2345"},
    )

    assert report.status == "FAIL"
    assert report.checks["expected_yield"] == "FAIL"
    assert report.checks["delete_sanity"] == "FAIL"
    assert report.checks["secrets_and_pii"] == "FAIL"
    assert len(report.errors) == 3


def test_run_checks_partial_fail_still_fails_overall() -> None:
    report = run_checks(
        detected_stacks=["sql_dbt"],
        counts_by_type={"Table": 1},
        tombstoned_count=40,
        previously_published_count=100,
        stored_texts={},
    )

    assert report.status == "FAIL"
    assert report.checks["expected_yield"] == "PASS"
    assert report.checks["delete_sanity"] == "FAIL"
    assert report.checks["secrets_and_pii"] == "PASS"
    assert len(report.errors) == 1
