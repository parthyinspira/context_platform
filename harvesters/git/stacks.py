"""Stack detection for the git harvester (KAN-78).

Detects which stacks (SQL/dbt, Java, .NET, Talend, shell, docs) are present
in a repository from marker files/extensions, per the table in
`docs/HARVESTERS.md` section 4 ("Git"). Include/exclude rules and size caps
per stack are *not* duplicated here: they are loaded from the YAML rules
built in KAN-79 (`harvesters.framework.stack_rules.load_stack_rules`), so
there is one source of truth for what a stack pulls and skips.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass


@dataclass(frozen=True)
class StackMarkers:
    """Marker glob patterns that identify a stack; matched against repo paths."""

    name: str
    markers: tuple[str, ...]


# `name` matches a `harvesters/rules/<name>.yaml` file (KAN-79 naming).
STACK_MARKERS: tuple[StackMarkers, ...] = (
    StackMarkers(name="sql_dbt", markers=("dbt_project.yml", "*.sql")),
    StackMarkers(name="java", markers=("pom.xml", "build.gradle", "build.gradle.kts")),
    StackMarkers(name="dotnet", markers=("*.sln", "*.csproj")),
    StackMarkers(name="talend", markers=("talend.project", "*.item", "*.properties")),
    StackMarkers(name="shell", markers=("*.sh", "*.ps1", "*.bat")),
)


def matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def detect_stacks(paths: list[str]) -> list[str]:
    """Return the names of every stack whose marker pattern matches at least one path."""
    detected: list[str] = []
    for stack in STACK_MARKERS:
        if matches_any_path(paths, stack.markers):
            detected.append(stack.name)
    return detected


def matches_any_path(paths: list[str], patterns: tuple[str, ...]) -> bool:
    return any(
        matches_any(p, patterns) or matches_any(p.rsplit("/", 1)[-1], patterns) for p in paths
    )
