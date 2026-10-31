"""Stack detection rules for the git harvester (KAN-78).

Mirrors the table in `docs/HARVESTERS.md` section 4 ("Git"): each stack is
detected by marker files/extensions, and has its own include/exclude glob
patterns (`fnmatch` syntax, matched against repo-relative paths). The
universal denylist applies regardless of detected stack.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass


@dataclass(frozen=True)
class StackRule:
    name: str
    markers: tuple[str, ...]  # glob patterns; any match detects the stack
    include: tuple[str, ...]
    exclude: tuple[str, ...] = ()


UNIVERSAL_EXCLUDE: tuple[str, ...] = (
    "*/.git/*",
    "*/node_modules/*",
    "*/vendor/*",
    "*.lock",
    "*.min.js",
    "*.min.css",
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.jar",
    "*.dll",
    "*.exe",
    "*.class",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
)

STACK_RULES: tuple[StackRule, ...] = (
    StackRule(
        name="sql-dbt",
        markers=("dbt_project.yml", "*.sql"),
        include=("*.sql", "schema.yml", "dbt_project.yml"),
        exclude=("*/seeds/*",),
    ),
    StackRule(
        name="java",
        markers=("pom.xml", "build.gradle"),
        include=("pom.xml", "build.gradle", "src/main/**/*.java", "*.sql", "src/main/resources/**"),
        exclude=("*/target/*", "*.jar", "*.class", "src/test/*"),
    ),
    StackRule(
        name="dotnet",
        markers=("*.sln", "*.csproj"),
        include=("*.sln", "*.csproj", "*.cs", "appsettings*.json", "*.sql"),
        exclude=("*/bin/*", "*/obj/*", "*.dll"),
    ),
    StackRule(
        name="talend",
        markers=("talend.project", "*.item", "*.properties"),
        include=("talend.project", "*.item", "*.properties"),
        exclude=("*.screenshot", "*.png", "*.jar", "*/lib/*", "*/screenshots/*"),
    ),
    StackRule(
        name="shell",
        markers=("*.sh", "*.ps1", "*.bat"),
        include=("*.sh", "*.ps1", "*.bat"),
        exclude=("*.log",),
    ),
)


def matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def detect_stacks(paths: list[str]) -> list[str]:
    """Return the names of every stack whose marker pattern matches at least one path."""
    detected: list[str] = []
    for rule in STACK_RULES:
        if any(
            matches_any(p, rule.markers) or matches_any(p.rsplit("/", 1)[-1], rule.markers)
            for p in paths
        ):
            detected.append(rule.name)
    return detected


def stack_rule(name: str) -> StackRule:
    for rule in STACK_RULES:
        if rule.name == name:
            return rule
    raise KeyError(f"no stack rule named '{name}'")
