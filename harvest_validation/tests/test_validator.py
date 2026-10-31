from harvest_validation.validator import (
    CheckStatus,
    check_delete_sanity,
    check_expected_yield,
    check_secrets_and_pii,
    run_checks,
)
from harvesters.base import ValidationReport

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

    assert isinstance(report, ValidationReport)
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
