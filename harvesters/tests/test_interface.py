import pytest

from harvesters.interface import (
    ConnectionResult,
    Entity,
    Harvester,
    HarvestPlan,
    HarvestRunState,
    Profile,
    RawObject,
    ScopeTree,
    ValidationReport,
)

EXPECTED_STAGES = {"connect", "discover", "profile", "plan", "harvest", "normalize", "validate"}


def test_harvester_declares_all_seven_stages():
    assert Harvester.__abstractmethods__ == EXPECTED_STAGES


def test_harvester_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Harvester()


def test_subclass_missing_a_method_cannot_be_instantiated():
    class Incomplete(Harvester):
        def connect(self, source):
            return ConnectionResult(ok=True)

        def discover(self, source):
            return ScopeTree()

        def profile(self, source, scope):
            return Profile(object_count=0, total_bytes=0)

        def plan(self, profile):
            return HarvestPlan()

        def harvest(self, source, plan, cursor):
            return []

        def normalize(self, raw):
            return []

        # validate() intentionally omitted

    with pytest.raises(TypeError):
        Incomplete()


class _FakeHarvester(Harvester):
    def connect(self, source):
        return ConnectionResult(ok=True)

    def discover(self, source):
        return ScopeTree()

    def profile(self, source, scope):
        return Profile(object_count=1, total_bytes=10)

    def plan(self, profile):
        return HarvestPlan(include=["*.sql"])

    def harvest(self, source, plan, cursor):
        return [RawObject(ref="a.sql", content=b"select 1;")]

    def normalize(self, raw):
        return [Entity(type="Table", name="a", external_id="a")]

    def validate(self, plan, manifest):
        return ValidationReport(status="PASS")


def test_complete_subclass_can_be_instantiated_and_run():
    harvester = _FakeHarvester()

    connection = harvester.connect(source=None)
    scope = harvester.discover(source=None)
    profile = harvester.profile(source=None, scope=scope)
    run_plan = harvester.plan(profile=profile)
    raw_objects = harvester.harvest(source=None, plan=run_plan, cursor=None)
    entities = [e for raw in raw_objects for e in harvester.normalize(raw)]
    report = harvester.validate(plan=run_plan, manifest=[])

    assert connection.ok is True
    assert len(raw_objects) == 1
    assert len(entities) == 1
    assert report.status == "PASS"


def test_harvest_run_states_match_the_migration_check_constraint():
    assert {s.value for s in HarvestRunState} == {
        "CONNECTING", "DISCOVERING", "PROFILING", "PLANNED", "APPROVED",
        "HARVESTING", "VALIDATING", "PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL",
    }
