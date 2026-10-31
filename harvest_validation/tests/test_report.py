from harvest_validation.gate import ValidationStatus
from harvest_validation.report import CheckResult, ValidationReport, build_report


def test_overall_status_is_pass_when_all_checks_pass():
    results = (
        CheckResult(name="completeness", status=ValidationStatus.PASS, message="ok"),
        CheckResult(name="freshness", status=ValidationStatus.PASS, message="ok"),
    )

    report = build_report(results)

    assert report.status == ValidationStatus.PASS


def test_overall_status_is_worst_of_warn_and_fail():
    results = (
        CheckResult(name="completeness", status=ValidationStatus.PASS, message="ok"),
        CheckResult(
            name="referential_integrity", status=ValidationStatus.WARN, message="dangling edge"
        ),
        CheckResult(
            name="ontology_conformance", status=ValidationStatus.FAIL, message="unknown type"
        ),
    )

    report = build_report(results)

    assert report.status == ValidationStatus.FAIL


def test_overall_status_is_pass_for_empty_checks():
    assert build_report(()).status == ValidationStatus.PASS


def test_report_check_looks_up_by_name():
    results = (CheckResult(name="freshness", status=ValidationStatus.WARN, message="stale"),)
    report = build_report(results)

    assert report.check("freshness").status == ValidationStatus.WARN


def test_report_check_raises_for_unknown_name():
    report = build_report(())
    try:
        report.check("nope")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")


def test_report_to_dict_includes_counts_and_samples():
    results = (
        CheckResult(
            name="completeness",
            status=ValidationStatus.WARN,
            message="ratio 0.9",
            counts={"fetched": 9, "discovered": 10},
            samples=("models/pending.sql",),
        ),
    )
    report = build_report(results)

    data = report.to_dict()

    assert data["status"] == "WARN"
    assert data["checks"][0]["counts"] == {"fetched": 9, "discovered": 10}
    assert data["checks"][0]["samples"] == ["models/pending.sql"]


def test_validation_report_default_checks_is_empty():
    assert ValidationReport(status=ValidationStatus.PASS).checks == ()
