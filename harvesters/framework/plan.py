"""Harvest plan model shared by every harvester (KAN-76).

A `HarvestPlan` is the output of a harvester's `plan()` step (see
`docs/HARVESTERS.md` section 1-2): rules turn a profile into include/exclude
patterns, a per-object size cap and run budgets, which the user approves
before `harvest()` runs.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Budgets:
    """Per-run limits. `None` means unlimited for that dimension."""

    max_files: int | None = None
    max_bytes: int | None = None
    max_seconds: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class HarvestPlan:
    """Include/exclude rules, a per-object size cap, and run budgets.

    `include`/`exclude` are glob patterns (`fnmatch` syntax) matched against
    an object's path. An empty `include` means "everything not excluded".
    Exclude always wins over include, per `docs/HARVESTERS.md` rule 5
    ("allowlist by purpose, denylist by noise").
    """

    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    size_cap_bytes: int | None = None
    budgets: Budgets = field(default_factory=Budgets)

    def is_included(self, path: str) -> bool:
        if any(fnmatch.fnmatch(path, pattern) for pattern in self.exclude):
            return False
        if not self.include:
            return True
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.include)
