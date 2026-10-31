"""Tests for the harvest plan model (KAN-76)."""
from harvesters.framework.plan import Budgets, HarvestPlan


def test_include_exclude_denylist_wins_over_allowlist() -> None:
    plan = HarvestPlan(include=("*.sql", "*.yml"), exclude=("*/target/*", "*.jar"))

    assert plan.is_included("models/staging/stg_orders.sql")
    assert plan.is_included("schema.yml")
    assert not plan.is_included("build/target/app.jar")
    assert not plan.is_included("lib/vendor.jar")


def test_no_include_patterns_means_everything_not_excluded_is_included() -> None:
    plan = HarvestPlan(exclude=("*.jar", "*/node_modules/*"))

    assert plan.is_included("src/app/Main.java")
    assert not plan.is_included("lib/app.jar")
    assert not plan.is_included("web/node_modules/pkg/index.js")


def test_not_in_include_list_is_excluded() -> None:
    plan = HarvestPlan(include=("*.sql",))

    assert not plan.is_included("README.md")


def test_default_plan_has_no_caps_or_budgets() -> None:
    plan = HarvestPlan()

    assert plan.include == ()
    assert plan.exclude == ()
    assert plan.size_cap_bytes is None
    assert plan.budgets == Budgets()


def test_plan_holds_caps_and_budgets() -> None:
    plan = HarvestPlan(
        include=("*.sql",),
        exclude=("*.jar",),
        size_cap_bytes=1_000_000,
        budgets=Budgets(max_files=1000, max_bytes=50_000_000, max_seconds=300, max_tokens=200_000),
    )

    assert plan.size_cap_bytes == 1_000_000
    assert plan.budgets.max_files == 1000
    assert plan.budgets.max_bytes == 50_000_000
    assert plan.budgets.max_seconds == 300
    assert plan.budgets.max_tokens == 200_000
