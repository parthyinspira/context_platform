import pytest

from harvest_validation.gate import (
    GateResult,
    InvalidRunStateError,
    PublishQuarantineGate,
    RunState,
    ValidationStatus,
)


class FakeKnowledgeStore:
    """Stands in for the graph store to prove FAIL leaves it untouched."""

    def __init__(self) -> None:
        self.published_entities = ["repo-a-table-1", "repo-a-table-2"]

    def apply(self, gate_result: GateResult, candidate_entities: list[str]) -> None:
        if gate_result.published:
            self.published_entities = candidate_entities


def test_failed_validation_quarantines_and_keeps_previous_knowledge() -> None:
    gate = PublishQuarantineGate()
    store = FakeKnowledgeStore()
    previous = list(store.published_entities)

    result = gate.evaluate(RunState.VALIDATING, ValidationStatus.FAIL)
    store.apply(result, candidate_entities=["new-but-bad-entity"])

    assert result.new_state == RunState.QUARANTINED
    assert result.published is False
    assert store.published_entities == previous


def test_warn_validation_publishes_with_warning() -> None:
    gate = PublishQuarantineGate()
    store = FakeKnowledgeStore()
    candidate = ["repo-a-table-1", "repo-a-table-2", "repo-a-table-3"]

    result = gate.evaluate(RunState.VALIDATING, ValidationStatus.WARN)
    store.apply(result, candidate_entities=candidate)

    assert result.new_state == RunState.PUBLISHED
    assert result.published is True
    assert result.warning is True
    assert store.published_entities == candidate


def test_pass_validation_publishes_without_warning() -> None:
    gate = PublishQuarantineGate()
    store = FakeKnowledgeStore()
    candidate = ["repo-a-table-1", "repo-a-table-2", "repo-a-table-3"]

    result = gate.evaluate(RunState.VALIDATING, ValidationStatus.PASS)
    store.apply(result, candidate_entities=candidate)

    assert result.new_state == RunState.PUBLISHED
    assert result.published is True
    assert result.warning is False
    assert store.published_entities == candidate


@pytest.mark.parametrize(
    "bad_state",
    [
        RunState.CONNECTING,
        RunState.DISCOVERING,
        RunState.PROFILING,
        RunState.PLANNED,
        RunState.APPROVED,
        RunState.HARVESTING,
        RunState.PUBLISHED,
        RunState.QUARANTINED,
        RunState.FAILED,
    ],
)
def test_gate_rejects_non_validating_state(bad_state: RunState) -> None:
    gate = PublishQuarantineGate()

    with pytest.raises(InvalidRunStateError):
        gate.evaluate(bad_state, ValidationStatus.PASS)


def test_gate_rejects_non_validating_state_even_on_fail_status() -> None:
    gate = PublishQuarantineGate()

    with pytest.raises(InvalidRunStateError):
        gate.evaluate(RunState.HARVESTING, ValidationStatus.FAIL)
