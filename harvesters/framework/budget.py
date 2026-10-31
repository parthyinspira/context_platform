"""Budget enforcement for a harvest run (KAN-76).

Per `docs/HARVESTERS.md` rule 3 ("Budgets per run"): on hitting a files,
bytes, time or token budget, the run stops cleanly, is marked `PARTIAL`, and
the report names the exceeded budget.
"""
from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar

from harvesters.framework.plan import Budgets

T = TypeVar("T")


class RunStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"


@dataclass
class BudgetUsage:
    files: int = 0
    bytes: int = 0
    tokens: int = 0
    started_at: float = field(default_factory=time.monotonic)


class BudgetExceeded(Exception):
    """Raised when processing the next object would exceed a budget."""

    def __init__(self, budget_name: str) -> None:
        self.budget_name = budget_name
        super().__init__(f"budget exceeded: {budget_name}")


class BudgetTracker:
    """Tracks consumption against `Budgets` and raises `BudgetExceeded` cleanly."""

    def __init__(self, budgets: Budgets, clock: Callable[[], float] = time.monotonic) -> None:
        self._budgets = budgets
        self._clock = clock
        self.usage = BudgetUsage(started_at=clock())

    def check_before_file(self) -> None:
        """Call before fetching the next object; stops the run before unaffordable work starts."""
        b = self._budgets
        if b.max_files is not None and self.usage.files + 1 > b.max_files:
            raise BudgetExceeded("files")
        if b.max_seconds is not None and (self._clock() - self.usage.started_at) > b.max_seconds:
            raise BudgetExceeded("time")

    def record_file(self, size_bytes: int = 0, tokens: int = 0) -> None:
        """Call after an object is fetched/processed; raises if a cumulative budget is now over."""
        b = self._budgets
        if b.max_bytes is not None and self.usage.bytes + size_bytes > b.max_bytes:
            raise BudgetExceeded("bytes")
        if b.max_tokens is not None and self.usage.tokens + tokens > b.max_tokens:
            raise BudgetExceeded("tokens")
        self.usage.files += 1
        self.usage.bytes += size_bytes
        self.usage.tokens += tokens


def run_with_budget(
    objects: Iterable[T],
    budgets: Budgets,
    process: Callable[[T], tuple[int, int]],
) -> tuple[RunStatus, BudgetUsage, str | None]:
    """Process `objects` under `budgets`, stopping cleanly on the first budget hit.

    `process(obj)` returns `(size_bytes, tokens)` consumed by that object.
    Returns `(status, usage, exceeded_budget_name)`; `exceeded_budget_name`
    is `None` when the run completed without hitting a budget.
    """
    tracker = BudgetTracker(budgets)
    for obj in objects:
        try:
            tracker.check_before_file()
            size_bytes, tokens = process(obj)
            tracker.record_file(size_bytes, tokens)
        except BudgetExceeded as exc:
            return RunStatus.PARTIAL, tracker.usage, exc.budget_name
    return RunStatus.COMPLETED, tracker.usage, None
