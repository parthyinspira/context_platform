"""Git harvester: partial-clone discovery, stack detection and profiling (KAN-78).

Implements the `connect`/`discover`/`profile`/`plan` slice of
`docs/HARVESTERS.md` section 4 ("Git"). `harvest()`, `normalize()` and
`validate()` are deferred to a follow-up Epic 3 story (see
`spec/changes/kan-78-git-profiler/proposal.md` "Out of scope").

Discovery never fetches blob content: it creates a blobless partial clone
(`git clone --filter=blob:none --sparse --no-checkout`) and lists files with
`git ls-tree -r -l HEAD`, which reads tree/size metadata without blob content.
"""
from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from harvesters.base import (
    Chunk,
    ConnectionResult,
    Edge,
    Entity,
    Harvester,
    Profile,
    RawObject,
    ScopeNode,
    ScopeTree,
    ValidationReport,
)
from harvesters.framework import Budgets, HarvestPlan
from harvesters.git.stacks import UNIVERSAL_EXCLUDE, detect_stacks, matches_any, stack_rule
from harvesters.registry import register_harvester

DEFAULT_SIZE_CAP_BYTES = 1_000_000
_GIT_TIMEOUT_SECONDS = 60


class GitConnectionError(RuntimeError):
    """`git` failed to connect or list a repository."""


def _run_git(args: list[str], cwd: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise GitConnectionError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


@dataclass
class GitProfile(Profile):
    """`Profile` extended with per-stack pull/skip byte estimates (KAN-78)."""

    estimated_pull_bytes_by_stack: dict[str, int] = field(default_factory=dict)
    estimated_skip_bytes: int = 0


@register_harvester("git")
class GitHarvester(Harvester):
    """Harvester for git repositories: SQL/dbt, Java, .NET, Talend, shell stacks."""

    def connect(self, source: Any) -> ConnectionResult:
        uri = _source_uri(source)
        try:
            _run_git(["ls-remote", "--exit-code", uri, "HEAD"])
        except GitConnectionError as exc:
            return ConnectionResult(ok=False, error=str(exc))
        except subprocess.TimeoutExpired:
            return ConnectionResult(ok=False, error="timed out contacting remote")
        return ConnectionResult(ok=True)

    def discover(self, source: Any) -> ScopeTree:
        uri = _source_uri(source)
        with tempfile.TemporaryDirectory(prefix="git-harvester-") as tmp:
            _run_git(
                [
                    "clone",
                    "--filter=blob:none",
                    "--sparse",
                    "--no-checkout",
                    "--depth",
                    "1",
                    uri,
                    tmp,
                ]
            )
            output = _run_git(["ls-tree", "-r", "-l", "HEAD"], cwd=tmp)
        nodes = [_parse_ls_tree_line(line) for line in output.splitlines() if line.strip()]
        return ScopeTree(roots=[n for n in nodes if n is not None])

    def profile(self, source: Any, scope: ScopeTree) -> GitProfile:
        refs = scope.refs()
        paths = [r.path for r in refs]
        detected = detect_stacks(paths)

        pull_bytes: dict[str, int] = {name: 0 for name in detected}
        skip_bytes = 0
        counts_by_type: dict[str, int] = {}

        for ref in refs:
            ext = Path(ref.path).suffix or "(none)"
            counts_by_type[ext] = counts_by_type.get(ext, 0) + 1

            if matches_any(ref.path, UNIVERSAL_EXCLUDE) or ref.size_bytes > DEFAULT_SIZE_CAP_BYTES:
                skip_bytes += ref.size_bytes
                continue

            pulled_by_a_stack = False
            for name in detected:
                rule = stack_rule(name)
                if matches_any(ref.path, rule.exclude):
                    continue
                if matches_any(ref.path, rule.include):
                    pull_bytes[name] += ref.size_bytes
                    pulled_by_a_stack = True
            if not pulled_by_a_stack:
                skip_bytes += ref.size_bytes

        return GitProfile(
            object_count=len(refs),
            total_bytes=sum(r.size_bytes for r in refs),
            detected_stacks=detected,
            counts_by_type=counts_by_type,
            estimated_pull_bytes_by_stack=pull_bytes,
            estimated_skip_bytes=skip_bytes,
        )

    def plan(self, profile: Profile) -> HarvestPlan:
        detected = profile.detected_stacks if isinstance(profile, GitProfile) else []
        include: list[str] = []
        exclude: list[str] = list(UNIVERSAL_EXCLUDE)
        for name in detected:
            rule = stack_rule(name)
            include.extend(rule.include)
            exclude.extend(rule.exclude)
        return HarvestPlan(
            include=tuple(dict.fromkeys(include)),
            exclude=tuple(dict.fromkeys(exclude)),
            size_cap_bytes=DEFAULT_SIZE_CAP_BYTES,
            budgets=Budgets(),
        )

    def harvest(
        self, source: Any, plan: HarvestPlan, cursor: Optional[str]
    ) -> Iterable[RawObject]:
        raise NotImplementedError(
            "GitHarvester.harvest() is deferred to the Epic 3 follow-up story "
            "that builds on KAN-78's discover/profile/plan"
        )

    def normalize(self, raw: RawObject) -> list[Entity | Edge | Chunk]:
        raise NotImplementedError(
            "GitHarvester.normalize() is deferred to the Epic 3 follow-up story "
            "that builds on KAN-78's discover/profile/plan"
        )

    def validate(
        self, plan: HarvestPlan, manifest: list[dict[str, Any]]
    ) -> ValidationReport:
        raise NotImplementedError(
            "GitHarvester.validate() is deferred to the Epic 3 follow-up story "
            "that builds on KAN-78's discover/profile/plan"
        )


def _source_uri(source: Any) -> str:
    if isinstance(source, dict):
        return source["uri"]
    return source.uri


def _parse_ls_tree_line(line: str) -> ScopeNode | None:
    """Parse one `git ls-tree -r -l` line: `<mode> <type> <sha>  <size>\\t<path>`."""
    meta, _, path = line.partition("\t")
    fields = meta.split()
    if len(fields) < 4 or fields[1] != "blob":
        return None
    size_field = fields[3]
    size_bytes = 0 if size_field == "-" else int(size_field)
    return ScopeNode(id=fields[2], kind="file", name=path, size_hint=size_bytes)
