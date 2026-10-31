"""Git sparse fetch: the `harvest()` step for Git sources (KAN-80).

Implements `docs/HARVESTERS.md` section 4 ("Git — do not clone fully") for
the *harvest* stage only: given an already-approved `HarvestPlan` and a
cursor (a commit SHA), fetch only the planned, under-cap paths, incrementally
since the cursor, and record every discovered path in the `Manifest`.

`connect`, `discover`, `profile` and `plan` for Git, and wiring this into the
`Harvester` registry under source type `"git"`, are separate stories; this
module is a plain function, not a `Harvester` subclass.

Uses a local partial bare clone (`git clone --bare --filter=blob:none`) so
blob content for excluded paths is never fetched from the remote — the
"sparse fetch" named in the plan's rules. Tree listing (`git ls-tree -r -l`)
gives paths and sizes without fetching blobs; only accepted paths are
retrieved with `git cat-file -p`.
"""
from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harvesters.base import RawObject
from harvesters.framework.budget import BudgetExceeded, BudgetTracker
from harvesters.framework.manifest import Manifest
from harvesters.framework.plan import HarvestPlan


class GitHarvestError(RuntimeError):
    """A git operation needed to harvest the source failed."""


@dataclass(frozen=True)
class GitHarvestResult:
    """Output of `harvest_git`: the fetched objects and the new cursor.

    `budget_exceeded` names the budget dimension that stopped the run early
    (`None` if every included, under-cap, changed path was fetched); the
    caller marks the `harvest_runs` row `PARTIAL` when it is set.
    """

    objects: list[RawObject]
    head_sha: str
    budget_exceeded: str | None = None


def _get(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _run_text(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise GitHarvestError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _run_bytes(args: list[str], cwd: Path) -> bytes:
    result = subprocess.run(args, cwd=cwd, capture_output=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        raise GitHarvestError(f"git {' '.join(args)} failed: {stderr}")
    return result.stdout


def _parse_ls_tree_line(line: str) -> tuple[str, int, str]:
    """Parse one `git ls-tree -r -l` line -> (path, size_bytes, blob_sha)."""
    meta, path = line.split("\t", 1)
    mode, obj_type, blob_sha, size = meta.split()
    if obj_type != "blob":
        raise GitHarvestError(f"unexpected tree entry type {obj_type!r} for {path!r}")
    return path, (0 if size == "-" else int(size)), blob_sha


def harvest_git(
    source: Any, plan: HarvestPlan, cursor: str | None, manifest: Manifest
) -> GitHarvestResult:
    """Fetch only `plan`-included, under-cap, changed-since-`cursor` paths.

    `source` needs a `uri` (local path or remote git URL) and may carry
    `config_json={"ref": "<branch-or-sha>"}` (defaults to `HEAD`).
    """
    uri = _get(source, "uri")
    if not uri:
        raise GitHarvestError("source has no uri")
    config = _get(source, "config_json") or {}
    ref = config.get("ref", "HEAD")

    with tempfile.TemporaryDirectory(prefix="git-harvest-") as tmp:
        repo = Path(tmp) / "repo.git"
        _run_text(
            ["git", "clone", "--bare", "--filter=blob:none", "--no-tags", str(uri), str(repo)],
            cwd=Path(tmp),
        )
        head_sha = _run_text(["git", "rev-parse", ref], cwd=repo).strip()

        changed_paths: set[str] | None = None
        if cursor:
            diff_out = _run_text(["git", "diff", "--name-only", cursor, head_sha], cwd=repo)
            changed_paths = {line.strip() for line in diff_out.splitlines() if line.strip()}

        tree_out = _run_text(["git", "ls-tree", "-r", "-l", head_sha], cwd=repo)
        tracker = BudgetTracker(plan.budgets)
        objects: list[RawObject] = []
        budget_exceeded: str | None = None

        for line in tree_out.splitlines():
            if not line.strip():
                continue
            path, size_bytes, blob_sha = _parse_ls_tree_line(line)
            manifest.discovered(path, "listed at target commit", size_bytes=size_bytes)

            if not plan.is_included(path):
                manifest.skipped(path, "excluded by plan")
                continue
            if plan.size_cap_bytes is not None and size_bytes > plan.size_cap_bytes:
                manifest.skipped(path, f"exceeds size cap of {plan.size_cap_bytes} bytes")
                continue
            if changed_paths is not None and path not in changed_paths:
                manifest.skipped(path, "unchanged since cursor")
                continue
            if budget_exceeded is not None:
                # Already stopped; remaining discovered paths stay unaccounted
                # (manifest.unaccounted()) for the validator's PARTIAL check.
                continue

            try:
                tracker.check_before_file()
                content = _run_bytes(["git", "cat-file", "-p", blob_sha], cwd=repo)
                tracker.record_file(size_bytes=len(content))
            except BudgetExceeded as exc:
                budget_exceeded = exc.budget_name
                continue

            objects.append(RawObject(external_id=path, content=content))
            manifest.fetched(path, "fetched at target commit")

        return GitHarvestResult(objects=objects, head_sha=head_sha, budget_exceeded=budget_exceeded)
