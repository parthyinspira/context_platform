"""Per-stack YAML harvest rules (KAN-79).

Turns the stack table in `docs/HARVESTERS.md` section 4 into a `HarvestPlan`
per stack: deterministic include/exclude globs and a per-object size cap. A
future harvester's `plan()` step looks these up once it has detected a
stack; stack detection itself is out of scope here.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from harvesters.framework.plan import HarvestPlan

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"

# Always excluded regardless of stack, per docs/HARVESTERS.md rule 5
# ("allowlist by purpose, denylist by noise").
COMMON_EXCLUDE: tuple[str, ...] = (
    ".git/*",
    "*/.git/*",
    "node_modules/*",
    "*/node_modules/*",
    "vendor/*",
    "*/vendor/*",
    "*.lock",
    "*.min.js",
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.7z",
)


class UnknownStackError(KeyError):
    """Raised when a stack name has no rules file under `harvesters/rules/`."""


def available_stacks() -> tuple[str, ...]:
    """Names of every stack with a rules file, sorted."""
    return tuple(sorted(path.stem for path in RULES_DIR.glob("*.yaml")))


def load_stack_rules(stack: str) -> HarvestPlan:
    """Load `harvesters/rules/<stack>.yaml` into a `HarvestPlan`."""
    path = RULES_DIR / f"{stack}.yaml"
    if not path.exists():
        raise UnknownStackError(stack)

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    include = tuple(data.get("include", ()))
    exclude = tuple(data.get("exclude", ())) + COMMON_EXCLUDE
    size_cap_bytes = data.get("size_cap_bytes")

    return HarvestPlan(include=include, exclude=exclude, size_cap_bytes=size_cap_bytes)
