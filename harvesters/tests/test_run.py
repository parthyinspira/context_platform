from typing import Iterable

import pytest

from harvesters.base import (
    Chunk,
    ConnectionResult,
    Edge,
    Entity,
    Harvester,
    HarvestRunState,
    Profile,
    RawObject,
    ScopeNode,
    ScopeTree,
    ValidationReport,
)
from harvesters.framework import HarvestPlan
from harvesters.registry import register_harvester
from harvesters.run import HarvestRunNotFoundError, RunnerError, main, parse_args, run
from harvesters.tests.fake_postgres import (
    FakeEventBus,
    FakeHarvestRun,
    FakePostgresConnection,
    FakeSource,
)

SOURCE_ID = "src-1"
PLAN_ID = "run-1"


class _RunnerTestHarvester(Harvester):
    """A controllable fixture harvester: class attributes decide connect/validate outcomes."""

    connect_ok = True
    validate_status = "PASS"

    def connect(self, source) -> ConnectionResult:
        return ConnectionResult(ok=self.connect_ok, error=None if self.connect_ok else "no auth")

    def discover(self, source) -> ScopeTree:
        return ScopeTree(roots=[ScopeNode(id="obj-1", kind="file", name="obj-1.txt", size_hint=5)])

    def profile(self, source, scope: ScopeTree) -> Profile:
        refs = scope.refs()
        return Profile(object_count=len(refs), total_bytes=sum(r.size_bytes for r in refs))

    def plan(self, profile: Profile) -> HarvestPlan:
        return HarvestPlan()

    def harvest(self, source, plan: HarvestPlan, cursor) -> Iterable[RawObject]:
        for ref in self.discover(source).refs():
            yield RawObject(external_id=ref.external_id, content=b"hi", content_type="text/plain")

    def normalize(self, raw: RawObject) -> list[Entity | Edge | Chunk]:
        return [Entity(type="Document", name=raw.external_id, external_id=raw.external_id)]

    def validate(self, plan: HarvestPlan, manifest) -> ValidationReport:
        errors = ["forced failure"] if self.validate_status == "FAIL" else []
        return ValidationReport(status=self.validate_status, errors=errors)


@register_harvester("runner-test-ok")
class OkHarvester(_RunnerTestHarvester):
    connect_ok = True
    validate_status = "PASS"


@register_harvester("runner-test-fail-validate")
class FailValidateHarvester(_RunnerTestHarvester):
    connect_ok = True
    validate_status = "FAIL"


@register_harvester("runner-test-no-connect")
class NoConnectHarvester(_RunnerTestHarvester):
    connect_ok = False


def _setup(source_type: str) -> tuple[FakePostgresConnection, FakeEventBus]:
    conn = FakePostgresConnection(
        sources={SOURCE_ID: FakeSource(id=SOURCE_ID, type=source_type)},
        runs={PLAN_ID: FakeHarvestRun(id=PLAN_ID, source_id=SOURCE_ID, plan={})},
    )
    return conn, FakeEventBus()


def test_runner_drives_full_lifecycle_to_published():
    conn, event_bus = _setup("runner-test-ok")

    final_state = run(SOURCE_ID, PLAN_ID, connection_factory=lambda: conn, event_bus=event_bus)

    assert final_state == HarvestRunState.PUBLISHED
    assert conn.state_history == ["HARVESTING", "VALIDATING", "PUBLISHED"]
    assert conn.runs[PLAN_ID].state == "PUBLISHED"
    [(topic, payload)] = event_bus.published
    assert topic == "harvest.completed"
    assert payload["run_id"] == PLAN_ID
    assert payload["source_id"] == SOURCE_ID
    assert payload["state"] == "PUBLISHED"
    assert payload["published"] is True
    assert payload["entity_count"] == 1


def test_runner_quarantines_on_failed_validation():
    conn, event_bus = _setup("runner-test-fail-validate")

    final_state = run(SOURCE_ID, PLAN_ID, connection_factory=lambda: conn, event_bus=event_bus)

    assert final_state == HarvestRunState.QUARANTINED
    assert conn.state_history == ["HARVESTING", "VALIDATING", "QUARANTINED"]
    assert conn.runs[PLAN_ID].error == "forced failure"
    [(topic, payload)] = event_bus.published
    assert topic == "harvest.completed"
    assert payload["published"] is False
    assert payload["state"] == "QUARANTINED"


def test_runner_fails_cleanly_on_connect_error():
    conn, event_bus = _setup("runner-test-no-connect")

    final_state = run(SOURCE_ID, PLAN_ID, connection_factory=lambda: conn, event_bus=event_bus)

    assert final_state == HarvestRunState.FAILED
    assert conn.state_history == ["HARVESTING", "FAILED"]
    assert "connect failed" in conn.runs[PLAN_ID].error
    [(topic, payload)] = event_bus.published
    assert topic == "harvest.completed"
    assert payload["state"] == "FAILED"
    assert payload["published"] is False


def test_runner_rejects_unknown_plan_id():
    conn = FakePostgresConnection(
        sources={SOURCE_ID: FakeSource(id=SOURCE_ID, type="runner-test-ok")}
    )
    event_bus = FakeEventBus()

    with pytest.raises(HarvestRunNotFoundError):
        run(SOURCE_ID, "no-such-run", connection_factory=lambda: conn, event_bus=event_bus)

    assert conn.state_history == []
    assert event_bus.published == []


def test_runner_rejects_unregistered_source_type():
    conn = FakePostgresConnection(
        sources={SOURCE_ID: FakeSource(id=SOURCE_ID, type="no-such-source-type")},
        runs={PLAN_ID: FakeHarvestRun(id=PLAN_ID, source_id=SOURCE_ID, plan={})},
    )
    event_bus = FakeEventBus()

    with pytest.raises(RunnerError):
        run(SOURCE_ID, PLAN_ID, connection_factory=lambda: conn, event_bus=event_bus)

    assert conn.state_history == []
    assert event_bus.published == []


def test_runner_rejects_plan_id_belonging_to_a_different_source():
    conn = FakePostgresConnection(
        sources={SOURCE_ID: FakeSource(id=SOURCE_ID, type="runner-test-ok")},
        runs={PLAN_ID: FakeHarvestRun(id=PLAN_ID, source_id="some-other-source", plan={})},
    )
    event_bus = FakeEventBus()

    with pytest.raises(HarvestRunNotFoundError):
        run(SOURCE_ID, PLAN_ID, connection_factory=lambda: conn, event_bus=event_bus)

    assert conn.state_history == []


def test_parse_args_reads_from_environment(monkeypatch):
    monkeypatch.setenv("SOURCE_ID", "env-source")
    monkeypatch.setenv("PLAN_ID", "env-plan")

    args = parse_args([])

    assert args.source_id == "env-source"
    assert args.plan_id == "env-plan"


def test_parse_args_cli_flags_override_environment(monkeypatch):
    monkeypatch.setenv("SOURCE_ID", "env-source")
    monkeypatch.setenv("PLAN_ID", "env-plan")

    args = parse_args(["--source-id", "cli-source", "--plan-id", "cli-plan"])

    assert args.source_id == "cli-source"
    assert args.plan_id == "cli-plan"


def test_parse_args_requires_source_id_and_plan_id(monkeypatch):
    monkeypatch.delenv("SOURCE_ID", raising=False)
    monkeypatch.delenv("PLAN_ID", raising=False)

    with pytest.raises(SystemExit):
        parse_args([])


def test_main_exits_zero_on_published(monkeypatch):
    conn, event_bus = _setup("runner-test-ok")
    monkeypatch.setattr(
        "harvesters.run.run",
        lambda source_id, plan_id: HarvestRunState.PUBLISHED,
    )

    exit_code = main(["--source-id", SOURCE_ID, "--plan-id", PLAN_ID])

    assert exit_code == 0


def test_main_exits_nonzero_on_failed(monkeypatch):
    monkeypatch.setattr(
        "harvesters.run.run",
        lambda source_id, plan_id: HarvestRunState.FAILED,
    )

    exit_code = main(["--source-id", SOURCE_ID, "--plan-id", PLAN_ID])

    assert exit_code == 1


def test_main_exits_two_on_runner_error(monkeypatch):
    def _raise(source_id, plan_id):
        raise RunnerError("DATABASE_URL must be set")

    monkeypatch.setattr("harvesters.run.run", _raise)

    exit_code = main(["--source-id", SOURCE_ID, "--plan-id", PLAN_ID])

    assert exit_code == 2
