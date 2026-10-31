"""`ValidationReport` and `CheckResult` (KAN-83).

The structure the seven checks in `harvest_validation/validator.py` populate,
per the "Report" requirement in `spec/capabilities/harvest-validation.md`:
every check shows a result, counts and sample failures, and the report's
overall `status` is whatever a `PublishQuarantineGate` (`harvest_validation/
gate.py`) can consume directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from harvest_validation.gate import ValidationStatus

# Severity order, worst first; used to pick the overall report status.
_SEVERITY = (ValidationStatus.FAIL, ValidationStatus.WARN, ValidationStatus.PASS)


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one validator check."""

    name: str
    status: ValidationStatus
    message: str
    counts: dict[str, int] = field(default_factory=dict)
    samples: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "counts": dict(self.counts),
            "samples": list(self.samples),
        }


@dataclass(frozen=True)
class ValidationReport:
    """Output of `validate()`: overall status plus every check's result."""

    status: ValidationStatus
    checks: tuple[CheckResult, ...] = ()

    def check(self, name: str) -> CheckResult:
        for result in self.checks:
            if result.name == name:
                return result
        raise KeyError(f"no check named {name!r} in this report")

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "checks": [c.to_dict() for c in self.checks],
        }


def overall_status(results: tuple[CheckResult, ...]) -> ValidationStatus:
    """The worst status among `results`; PASS if `results` is empty."""
    statuses = {r.status for r in results}
    for severity in _SEVERITY:
        if severity in statuses:
            return severity
    return ValidationStatus.PASS


def build_report(results: tuple[CheckResult, ...]) -> ValidationReport:
    return ValidationReport(status=overall_status(results), checks=results)
