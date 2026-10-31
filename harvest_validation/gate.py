"""Publish-or-quarantine gate (KAN-85).

Pure decision logic that turns a validator's PASS/WARN/FAIL status into a
run-state transition. Framework-independent: no `harvest_runs` table or
harvester exists yet (see `docs/HARVESTERS.md` section 5 and
`spec/capabilities/harvest-validation.md`), so this accepts and returns plain
values a future orchestrator can persist.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RunState(str, Enum):
    CONNECTING = "CONNECTING"
    DISCOVERING = "DISCOVERING"
    PROFILING = "PROFILING"
    PLANNED = "PLANNED"
    APPROVED = "APPROVED"
    HARVESTING = "HARVESTING"
    VALIDATING = "VALIDATING"
    PUBLISHED = "PUBLISHED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class InvalidRunStateError(ValueError):
    """Raised when the gate is asked to evaluate a run that is not VALIDATING."""


@dataclass(frozen=True)
class GateResult:
    new_state: RunState
    published: bool
    warning: bool
    reason: str


class PublishQuarantineGate:
    """Decides whether a run's knowledge is published or quarantined."""

    def evaluate(self, current_state: RunState, validation_status: ValidationStatus) -> GateResult:
        if current_state != RunState.VALIDATING:
            raise InvalidRunStateError(
                f"gate can only evaluate a run in state {RunState.VALIDATING}, "
                f"got {current_state}"
            )

        if validation_status == ValidationStatus.FAIL:
            return GateResult(
                new_state=RunState.QUARANTINED,
                published=False,
                warning=False,
                reason="validation FAILED: previous knowledge stays published, run quarantined",
            )

        if validation_status == ValidationStatus.WARN:
            return GateResult(
                new_state=RunState.PUBLISHED,
                published=True,
                warning=True,
                reason="validation WARN: published with warning",
            )

        return GateResult(
            new_state=RunState.PUBLISHED,
            published=True,
            warning=False,
            reason="validation PASS: published",
        )
