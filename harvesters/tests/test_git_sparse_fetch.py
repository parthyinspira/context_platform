"""Tests for the Git sparse fetch harvest step (KAN-80)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from harvesters.framework.manifest import Manifest, Outcome
from harvesters.framework.plan import Budgets, HarvestPlan
from harvesters.git.sparse_fetch import harvest_git


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "origin"
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "Test"], repo)
    return repo


def _commit(repo: Path, message: str) -> str:
    _git(["add", "-A"], repo)
    _git(["commit", "-q", "-m", message], repo)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def manifest() -> Manifest:
    return Manifest(source_id="src-git-1", run_id="run-1")


def test_excluded_and_oversize_paths_are_never_fetched(tmp_path: Path, manifest: Manifest) -> None:
    repo = _init_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src" / "App.java").write_text("class App {}\n")
    (repo / "target").mkdir()
    (repo / "target" / "App.class").write_bytes(b"\x00compiled")
    (repo / "big.sql").write_text("x" * 2048)
    sha = _commit(repo, "initial")

    plan = HarvestPlan(exclude=("target/*",), size_cap_bytes=1024)
    source = {"uri": str(repo)}

    result = harvest_git(source, plan, cursor=None, manifest=manifest)

    fetched_paths = {o.external_id for o in result.objects}
    assert fetched_paths == {"src/App.java"}
    assert result.head_sha == sha
    assert result.budget_exceeded is None

    skipped = {e.ref: e.outcome_reason for e in manifest.by_outcome(Outcome.SKIPPED)}
    assert "excluded by plan" == skipped["target/App.class"]
    assert "exceeds size cap of 1024 bytes" == skipped["big.sql"]


def test_incremental_by_commit_sha(tmp_path: Path, manifest: Manifest) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.sql").write_text("select 1;\n")
    (repo / "b.sql").write_text("select 2;\n")
    sha_a = _commit(repo, "first")

    (repo / "a.sql").write_text("select 1, 2;\n")
    sha_b = _commit(repo, "second")

    plan = HarvestPlan()
    source = {"uri": str(repo)}
    manifest_run2 = Manifest(source_id="src-git-1", run_id="run-2")

    result = harvest_git(source, plan, cursor=sha_a, manifest=manifest_run2)

    fetched_paths = {o.external_id for o in result.objects}
    assert fetched_paths == {"a.sql"}
    assert result.head_sha == sha_b
    assert manifest_run2.get("b.sql").outcome_reason == "unchanged since cursor"
    assert manifest_run2.get("a.sql").outcome_reason == "fetched at target commit"


def test_size_cap_enforced(tmp_path: Path, manifest: Manifest) -> None:
    repo = _init_repo(tmp_path)
    (repo / "small.txt").write_text("ok\n")
    (repo / "large.txt").write_text("x" * 2048)
    _commit(repo, "initial")

    plan = HarvestPlan(size_cap_bytes=1024)
    source = {"uri": str(repo)}

    result = harvest_git(source, plan, cursor=None, manifest=manifest)

    assert {o.external_id for o in result.objects} == {"small.txt"}
    entry = manifest.get("large.txt")
    assert entry.outcome.value == "skipped"
    assert "size cap" in entry.outcome_reason


def test_every_discovered_path_has_one_manifest_entry(tmp_path: Path, manifest: Manifest) -> None:
    repo = _init_repo(tmp_path)
    (repo / "keep.sql").write_text("select 1;\n")
    (repo / "skip").mkdir()
    (repo / "skip" / "noise.bin").write_bytes(b"\x00\x01")
    _commit(repo, "initial")

    plan = HarvestPlan(exclude=("skip/*",))
    source = {"uri": str(repo)}

    harvest_git(source, plan, cursor=None, manifest=manifest)

    counts = manifest.counts()
    assert counts["discovered"] == 2
    assert counts["unaccounted"] == 0
    for entry in manifest.entries():
        assert entry.outcome is not None
        assert entry.outcome_reason


def test_budget_stops_cleanly_and_leaves_remaining_unaccounted(
    tmp_path: Path, manifest: Manifest
) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("one\n")
    (repo / "b.txt").write_text("two\n")
    _commit(repo, "initial")

    plan = HarvestPlan(budgets=Budgets(max_files=1))
    source = {"uri": str(repo)}

    result = harvest_git(source, plan, cursor=None, manifest=manifest)

    assert len(result.objects) == 1
    assert result.budget_exceeded == "files"
    assert len(manifest.unaccounted()) == 1
