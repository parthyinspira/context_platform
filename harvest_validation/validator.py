"""Validator checks: expected yield, delete sanity, secrets/PII (KAN-84).

Implements three of the ten checks in `docs/HARVESTERS.md` section 5 and
`spec/capabilities/harvest-validation.md` ("Standard checks" / "Delete
sanity"). The other seven checks (completeness, exclusion integrity, budget
compliance, parse success, ontology conformance, referential integrity,
freshness) need a real manifest-driven harvester run to check against and are
a separate story (see `proposal.md`).

Each check is a pure function with no I/O, so it can be unit tested without a
harvester, a `Manifest`, or an `ObjectStore`. `run_checks` composes the three
into a `harvesters.base.ValidationReport`, the shape `Harvester.validate()`
already returns, so a future orchestrator can merge in the remaining checks
without a new report type.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from adapters.scanning import scan_and_redact
from harvesters.base import ValidationReport

DEFAULT_DELETE_SPIKE_THRESHOLD = 0.2  # 20%, per the capability spec's delete-spike scenario

# Stack -> ontology entity types that stack's detection is expected to yield at
# least one of, per the "Pull" column in docs/HARVESTERS.md section 4 ("Git").
# Stacks not listed here have no defined expectation and are skipped.
STACK_EXPECTED_ENTITY_TYPES: Mapping[str, frozenset[str]] = {
    "sql_dbt": frozenset({"Table"}),
    "java": frozenset({"Module"}),
    "dotnet": frozenset({"Module"}),
    "talend": frozenset({"Job"}),
    "shell": frozenset({"Module"}),
    "docs": frozenset({"Document"}),
}


class CheckStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CheckResult:
    status: CheckStatus
    detail: str
    counts: dict[str, int] = field(default_factory=dict)


def check_expected_yield(
    detected_stacks: Sequence[str], counts_by_type: Mapping[str, int]
) -> CheckResult:
    """Zero total yield fails outright; a detected stack with no entities of
    its expected type also fails, naming the stack."""
    total_yield = sum(counts_by_type.values())
    if total_yield == 0:
        return CheckResult(
            status=CheckStatus.FAIL,
            detail="zero entities emitted for a run with a non-empty scope",
            counts=dict(counts_by_type),
        )

    missing_stacks = [
        stack
        for stack in detected_stacks
        if stack in STACK_EXPECTED_ENTITY_TYPES
        and not any(counts_by_type.get(t, 0) > 0 for t in STACK_EXPECTED_ENTITY_TYPES[stack])
    ]
    if missing_stacks:
        return CheckResult(
            status=CheckStatus.FAIL,
            detail=f"no expected entities for detected stack(s): {', '.join(missing_stacks)}",
            counts=dict(counts_by_type),
        )

    return CheckResult(
        status=CheckStatus.PASS,
        detail="expected entity types present for every detected stack",
        counts=dict(counts_by_type),
    )


def check_delete_sanity(
    tombstoned_count: int,
    previously_published_count: int,
    threshold: float = DEFAULT_DELETE_SPIKE_THRESHOLD,
) -> CheckResult:
    """A tombstone share above `threshold` of what was previously published fails
    (the gate quarantines a FAIL, per `PublishQuarantineGate`)."""
    counts = {
        "tombstoned": tombstoned_count,
        "previously_published": previously_published_count,
    }
    if previously_published_count <= 0:
        return CheckResult(
            status=CheckStatus.PASS,
            detail="nothing previously published to compare against",
            counts=counts,
        )

    share = tombstoned_count / previously_published_count
    if share > threshold:
        return CheckResult(
            status=CheckStatus.FAIL,
            detail=(
                f"delete spike: {share:.0%} of previously published objects would be "
                f"tombstoned (threshold {threshold:.0%})"
            ),
            counts=counts,
        )

    return CheckResult(
        status=CheckStatus.PASS,
        detail=f"tombstone share {share:.0%} within threshold {threshold:.0%}",
        counts=counts,
    )


def check_secrets_and_pii(stored_texts: Mapping[str, str]) -> CheckResult:
    """Re-scans what was actually stored for each ref; fails naming any ref
    where a secret pattern is still present, unredacted."""
    offenders = sorted(
        ref for ref, text in stored_texts.items() if scan_and_redact(text).has_secrets
    )
    if offenders:
        return CheckResult(
            status=CheckStatus.FAIL,
            detail=f"unredacted secrets found in stored content: {', '.join(offenders)}",
            counts={"offending_objects": len(offenders)},
        )

    return CheckResult(
        status=CheckStatus.PASS,
        detail="no unredacted secrets found in stored content",
        counts={"offending_objects": 0},
    )


def run_checks(
    *,
    detected_stacks: Sequence[str],
    counts_by_type: Mapping[str, int],
    tombstoned_count: int,
    previously_published_count: int,
    stored_texts: Mapping[str, str],
    delete_spike_threshold: float = DEFAULT_DELETE_SPIKE_THRESHOLD,
) -> ValidationReport:
    """Runs the three checks in scope for this story and composes a `ValidationReport`.

    `status` is FAIL if any check fails, else PASS (no check here returns WARN
    yet; the other seven checks, out of scope, are what can produce WARN).
    """
    results = {
        "expected_yield": check_expected_yield(detected_stacks, counts_by_type),
        "delete_sanity": check_delete_sanity(
            tombstoned_count, previously_published_count, delete_spike_threshold
        ),
        "secrets_and_pii": check_secrets_and_pii(stored_texts),
    }

    checks = {name: result.status.value for name, result in results.items()}
    errors = [result.detail for result in results.values() if result.status == CheckStatus.FAIL]
    status = "FAIL" if errors else "PASS"

    return ValidationReport(status=status, checks=checks, errors=errors)
