"""Tests for budget enforcement during a harvest run (KAN-76)."""
from harvesters.framework.budget import (
    BudgetExceeded,
    BudgetTracker,
    RunStatus,
    run_with_budget,
)
from harvesters.framework.plan import Budgets


def test_file_budget_hit_stops_cleanly_and_marks_partial() -> None:
    objects = [f"file-{i}" for i in range(1500)]

    def process(_obj: str) -> tuple[int, int]:
        return (0, 0)

    status, usage, exceeded = run_with_budget(objects, Budgets(max_files=1000), process)

    assert status == RunStatus.PARTIAL
    assert exceeded == "files"
    assert usage.files == 1000


def test_byte_budget_hit_stops_cleanly_and_marks_partial() -> None:
    objects = list(range(10))

    def process(_obj: int) -> tuple[int, int]:
        return (300, 0)

    status, usage, exceeded = run_with_budget(objects, Budgets(max_bytes=1000), process)

    assert status == RunStatus.PARTIAL
    assert exceeded == "bytes"
    assert usage.bytes <= 1000


def test_token_budget_hit_stops_cleanly_and_marks_partial() -> None:
    objects = list(range(10))

    def process(_obj: int) -> tuple[int, int]:
        return (0, 500)

    status, usage, exceeded = run_with_budget(objects, Budgets(max_tokens=1200), process)

    assert status == RunStatus.PARTIAL
    assert exceeded == "tokens"


def test_time_budget_hit_stops_cleanly_and_marks_partial() -> None:
    objects = list(range(5))
    clock = iter([0.0, 0.0, 100.0, 100.0, 100.0, 100.0, 100.0])

    def process(_obj: int) -> tuple[int, int]:
        return (0, 0)

    tracker = BudgetTracker(Budgets(max_seconds=10), clock=lambda: next(clock))
    processed = 0
    exceeded_name = None
    for obj in objects:
        try:
            tracker.check_before_file()
            size, tokens = process(obj)
            tracker.record_file(size, tokens)
            processed += 1
        except BudgetExceeded as exc:
            exceeded_name = exc.budget_name
            break

    assert exceeded_name == "time"
    assert processed < len(objects)


def test_run_completes_when_no_budget_is_hit() -> None:
    objects = list(range(10))

    def process(_obj: int) -> tuple[int, int]:
        return (10, 5)

    budgets = Budgets(max_files=100, max_bytes=1000)
    status, usage, exceeded = run_with_budget(objects, budgets, process)

    assert status == RunStatus.COMPLETED
    assert exceeded is None
    assert usage.files == 10
    assert usage.bytes == 100


def test_report_names_the_exceeded_budget() -> None:
    objects = list(range(5))

    def process(_obj: int) -> tuple[int, int]:
        return (0, 0)

    _status, _usage, exceeded = run_with_budget(objects, Budgets(max_files=2), process)

    assert exceeded == "files"
