"""Tests for per-stack YAML harvest rules (KAN-79)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from harvesters.framework.plan import HarvestPlan
from harvesters.framework.stack_rules import (
    UnknownStackError,
    available_stacks,
    load_stack_rules,
)

FIXTURES_ROOT = Path(__file__).resolve().parent.parent.parent / "fixtures" / "repos"


def _relative_file_paths(root: Path) -> list[str]:
    return [
        str(path.relative_to(root)).replace(os.sep, "/")
        for path in root.rglob("*")
        if path.is_file()
    ]


def test_available_stacks_lists_all_six() -> None:
    assert set(available_stacks()) == {
        "sql_dbt",
        "java",
        "dotnet",
        "talend",
        "shell",
        "docs",
    }


def test_unknown_stack_raises() -> None:
    with pytest.raises(UnknownStackError):
        load_stack_rules("cobol")


def test_each_stack_returns_a_harvest_plan_with_size_cap() -> None:
    for stack in available_stacks():
        plan = load_stack_rules(stack)
        assert isinstance(plan, HarvestPlan)
        assert plan.include
        assert plan.size_cap_bytes == 1_048_576


def test_talend_fixture_plans_only_item_and_properties_files() -> None:
    plan = load_stack_rules("talend")
    paths = _relative_file_paths(FIXTURES_ROOT / "talend-sample")

    included = {path for path in paths if plan.is_included(path)}

    assert included == {"jobs/load_orders.item", "jobs/load_orders.properties"}
    assert "lib/talend-runtime.jar" not in included
    assert "screenshots/load_orders.png" not in included
    assert "talend.project" not in included
    assert "README.md" not in included


def test_java_fixture_excludes_target_and_includes_source_and_build_files() -> None:
    plan = load_stack_rules("java")
    paths = _relative_file_paths(FIXTURES_ROOT / "java-sample")
    included = {path for path in paths if plan.is_included(path)}

    assert "pom.xml" in included
    assert "src/main/java/com/inspira/sample/OrdersRepository.java" in included
    assert "src/main/resources/orders.sql" in included
    assert not any(path.startswith("target/") for path in included)


def test_dotnet_fixture_excludes_bin_and_obj_and_includes_source_and_config() -> None:
    plan = load_stack_rules("dotnet")
    paths = _relative_file_paths(FIXTURES_ROOT / "dotnet-sample")
    included = {path for path in paths if plan.is_included(path)}

    assert "SampleApp.sln" in included
    assert "SampleApp.csproj" in included
    assert "OrdersService.cs" in included
    assert "appsettings.json" in included
    assert not any(path.startswith("bin/") or path.startswith("obj/") for path in included)


def test_sql_dbt_fixture_includes_models_and_schema() -> None:
    plan = load_stack_rules("sql_dbt")
    paths = _relative_file_paths(FIXTURES_ROOT / "sql-dbt-sample")
    included = {path for path in paths if plan.is_included(path)}

    assert "models/staging/stg_orders.sql" in included
    assert "models/marts/mart_orders.sql" in included
    assert "seeds/source_orders.sql" in included
    assert "schema.yml" in included
    assert "dbt_project.yml" in included


def test_shell_rule_includes_scripts_and_excludes_logs() -> None:
    plan = load_stack_rules("shell")

    assert plan.is_included("scripts/export_orders.sh")
    assert plan.is_included("scripts/deploy.ps1")
    assert not plan.is_included("scripts/export_orders.log")


def test_docs_rule_includes_markdown_and_readme_and_excludes_images() -> None:
    plan = load_stack_rules("docs")

    assert plan.is_included("docs/data-retention-policy.md")
    assert plan.is_included("README.md")
    assert not plan.is_included("docs/diagram.png")
