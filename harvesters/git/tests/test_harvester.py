from pathlib import Path

import pytest

import harvesters  # noqa: F401  (registers GitHarvester)
from harvesters.git.harvester import DEFAULT_SIZE_CAP_BYTES, GitHarvester, GitProfile
from harvesters.git.tests.gitrepo import build_repo_from_fixture
from harvesters.registry import get_harvester

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "repos"


@pytest.fixture
def sql_dbt_repo(tmp_path):
    return build_repo_from_fixture(FIXTURES / "sql-dbt-sample", tmp_path / "repo")


@pytest.fixture
def java_repo(tmp_path):
    return build_repo_from_fixture(FIXTURES / "java-sample", tmp_path / "repo")


@pytest.fixture
def dotnet_repo(tmp_path):
    return build_repo_from_fixture(FIXTURES / "dotnet-sample", tmp_path / "repo")


@pytest.fixture
def talend_repo(tmp_path):
    return build_repo_from_fixture(FIXTURES / "talend-sample", tmp_path / "repo")


def test_registered_for_git_source_type():
    assert isinstance(get_harvester("git"), GitHarvester)


def test_connect_ok_for_reachable_repo(sql_dbt_repo):
    result = GitHarvester().connect({"uri": sql_dbt_repo})
    assert result.ok is True


def test_connect_fails_for_unreachable_repo(tmp_path):
    result = GitHarvester().connect({"uri": str(tmp_path / "does-not-exist")})
    assert result.ok is False
    assert result.error


def test_discover_lists_files_and_sizes_without_full_clone(sql_dbt_repo):
    scope = GitHarvester().discover({"uri": sql_dbt_repo})
    refs = {r.path: r.size_bytes for r in scope.refs()}
    assert "models/staging/stg_orders.sql" in refs
    assert "dbt_project.yml" in refs
    assert all(size >= 0 for size in refs.values())
    assert any(size > 0 for size in refs.values())


def test_discover_clone_uses_blob_none_filter_and_no_checkout(sql_dbt_repo, monkeypatch):
    calls = []
    import subprocess as sp

    original_run = sp.run

    def spy_run(args, **kwargs):
        calls.append(args)
        return original_run(args, **kwargs)

    monkeypatch.setattr("harvesters.git.harvester.subprocess.run", spy_run)
    GitHarvester().discover({"uri": sql_dbt_repo})
    clone_calls = [c for c in calls if c[:2] == ["git", "clone"]]
    assert len(clone_calls) == 1
    assert "--filter=blob:none" in clone_calls[0]
    assert "--no-checkout" in clone_calls[0]


def test_profile_detects_sql_dbt_stack(sql_dbt_repo):
    h = GitHarvester()
    scope = h.discover({"uri": sql_dbt_repo})
    profile = h.profile({"uri": sql_dbt_repo}, scope)
    assert isinstance(profile, GitProfile)
    assert "sql_dbt" in profile.detected_stacks


def test_profile_detects_java_stack_and_excludes_target(java_repo):
    h = GitHarvester()
    scope = h.discover({"uri": java_repo})
    profile = h.profile({"uri": java_repo}, scope)
    assert "java" in profile.detected_stacks
    target_bytes = sum(
        r.size_bytes for r in scope.refs() if r.path.startswith("target/")
    )
    assert target_bytes > 0
    def is_java_pull(path: str) -> bool:
        if path.startswith("target/"):
            return False
        return path.endswith(".java") or path in ("pom.xml",) or path.endswith(".sql")

    assert profile.estimated_pull_bytes_by_stack.get("java", 0) == sum(
        r.size_bytes for r in scope.refs() if is_java_pull(r.path)
    )
    assert profile.estimated_skip_bytes >= target_bytes


def test_profile_detects_dotnet_stack_and_excludes_bin_obj(dotnet_repo):
    h = GitHarvester()
    scope = h.discover({"uri": dotnet_repo})
    profile = h.profile({"uri": dotnet_repo}, scope)
    assert "dotnet" in profile.detected_stacks
    bin_obj_bytes = sum(
        r.size_bytes
        for r in scope.refs()
        if r.path.startswith("bin/") or r.path.startswith("obj/")
    )
    assert bin_obj_bytes > 0
    assert profile.estimated_skip_bytes >= bin_obj_bytes


def test_profile_detects_talend_stack_and_excludes_screenshots_and_lib(talend_repo):
    h = GitHarvester()
    scope = h.discover({"uri": talend_repo})
    profile = h.profile({"uri": talend_repo}, scope)
    assert "talend" in profile.detected_stacks
    denylisted_bytes = sum(
        r.size_bytes
        for r in scope.refs()
        if r.path.startswith("screenshots/") or r.path.startswith("lib/")
    )
    assert denylisted_bytes > 0
    assert profile.estimated_skip_bytes >= denylisted_bytes
    assert profile.estimated_pull_bytes_by_stack["talend"] > 0


def test_profile_estimate_totals_are_consistent(sql_dbt_repo):
    h = GitHarvester()
    scope = h.discover({"uri": sql_dbt_repo})
    profile = h.profile({"uri": sql_dbt_repo}, scope)
    pulled = sum(profile.estimated_pull_bytes_by_stack.values())
    assert pulled + profile.estimated_skip_bytes <= profile.total_bytes + pulled
    assert pulled <= profile.total_bytes
    assert profile.estimated_skip_bytes <= profile.total_bytes


def test_plan_includes_detected_stack_patterns(sql_dbt_repo):
    h = GitHarvester()
    scope = h.discover({"uri": sql_dbt_repo})
    profile = h.profile({"uri": sql_dbt_repo}, scope)
    plan = h.plan(profile)
    assert "*.sql" in plan.include
    assert plan.size_cap_bytes == DEFAULT_SIZE_CAP_BYTES
    assert "*/.git/*" in plan.exclude


def test_harvest_delegates_to_sparse_fetch(sql_dbt_repo):
    h = GitHarvester()
    scope = h.discover({"uri": sql_dbt_repo})
    profile = h.profile({"uri": sql_dbt_repo}, scope)
    plan = h.plan(profile)
    objects = list(h.harvest({"uri": sql_dbt_repo, "id": "src-1"}, plan, None))
    fetched_paths = {o.external_id for o in objects}
    assert "models/staging/stg_orders.sql" in fetched_paths


def test_normalize_validate_not_yet_implemented():
    h = GitHarvester()
    with pytest.raises(NotImplementedError):
        h.normalize(None)
    with pytest.raises(NotImplementedError):
        h.validate(h.plan(GitProfile(object_count=0, total_bytes=0)), [])
