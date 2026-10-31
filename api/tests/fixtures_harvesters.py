"""Harvester fixtures registered only for api/tests, following the pattern in
`harvesters/tests/fixtures.py` (fake source types so the real registry stays clean).
"""
from __future__ import annotations

from typing import Any, Iterable

from harvesters.base import (
    ConnectionResult,
    Profile,
    RawObject,
    ScopeNode,
    ScopeTree,
)
from harvesters.framework import Budgets, HarvestPlan
from harvesters.registry import register_harvester

from harvesters.tests.fixtures import FixtureHarvester


@register_harvester("api-test-ok")
class OkHarvester(FixtureHarvester):
    """Connects fine; discovers one 100-byte object; plan has no budgets."""

    def discover(self, source: dict) -> ScopeTree:
        return ScopeTree(
            roots=[ScopeNode(id="obj-1", kind="file", name="obj-1.txt", size_hint=100)]
        )


@register_harvester("api-test-connect-fail")
class ConnectFailHarvester(FixtureHarvester):
    def connect(self, source: dict) -> ConnectionResult:
        return ConnectionResult(ok=False, error="bad credentials")


@register_harvester("api-test-tight-budget")
class TightBudgetHarvester(FixtureHarvester):
    """Discovers one 100-byte object but plans a 5-byte budget, to exercise warnings."""

    def discover(self, source: dict) -> ScopeTree:
        return ScopeTree(
            roots=[ScopeNode(id="obj-1", kind="file", name="obj-1.txt", size_hint=100)]
        )

    def plan(self, profile: Profile) -> HarvestPlan:
        return HarvestPlan(budgets=Budgets(max_bytes=5))
