"""Test helper: build a local git repository from a fixture directory.

Used so harvester tests exercise the real `git clone --filter=blob:none`
partial-clone path against a real repository, without any live network
source. `uploadpack.allowfilter` must be enabled explicitly for local/file
transports; real git hosts (GitHub, GitLab, Azure DevOps, Bitbucket) enable
partial clone by default.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def build_repo_from_fixture(fixture_dir: Path, dest_dir: Path) -> str:
    """Copy `fixture_dir` into `dest_dir`, commit it, and return the repo path (a git URI)."""
    shutil.copytree(fixture_dir, dest_dir)
    _git(dest_dir, ["init", "-q", "-b", "main"])
    _git(dest_dir, ["config", "uploadpack.allowfilter", "true"])
    _git(dest_dir, ["config", "user.email", "test@example.com"])
    _git(dest_dir, ["config", "user.name", "test"])
    _git(dest_dir, ["add", "-A"])
    _git(dest_dir, ["commit", "-q", "-m", "fixture commit"])
    return str(dest_dir)


def _git(cwd: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout
