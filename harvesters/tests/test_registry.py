import pytest

from harvesters.registry import UnknownSourceTypeError, get_harvester, register_harvester

# Importing the fixtures module registers "fixture-type-a" and "fixture-type-b".
from harvesters.tests import fixtures  # noqa: F401


def test_registry_lookup_by_type_returns_instance_of_registered_class():
    harvester = get_harvester("fixture-type-a")
    assert isinstance(harvester, fixtures.RegisteredHarvesterA)


def test_registry_lookup_is_per_type():
    a = get_harvester("fixture-type-a")
    b = get_harvester("fixture-type-b")
    assert isinstance(a, fixtures.RegisteredHarvesterA)
    assert isinstance(b, fixtures.RegisteredHarvesterB)
    assert type(a) is not type(b)


def test_unknown_type_raises_with_type_name():
    with pytest.raises(UnknownSourceTypeError) as exc:
        get_harvester("does-not-exist")
    assert "does-not-exist" in str(exc.value)


def test_duplicate_registration_rejected():
    @register_harvester("fixture-type-dup")
    class First(fixtures.FixtureHarvester):
        pass

    with pytest.raises(ValueError):

        @register_harvester("fixture-type-dup")
        class Second(fixtures.FixtureHarvester):
            pass
