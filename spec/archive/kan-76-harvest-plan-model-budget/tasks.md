# Tasks

- [x] 1. Write `harvesters/tests/test_plan.py` (scenarios: include-exclude-precedence, plan-holds-caps-and-budgets, default-plan-is-unrestricted) - test first
- [x] 2. Add `harvesters/framework/plan.py`: `Budgets` and `HarvestPlan` dataclasses with `is_included(path)`
- [x] 3. Write `harvesters/tests/test_budget.py` (scenarios: budget hit for files/bytes/tokens/time stops cleanly and is marked PARTIAL naming the budget, run completes when no budget is hit) - test first
- [x] 4. Add `harvesters/framework/budget.py`: `BudgetTracker`, `BudgetExceeded`, `RunStatus`, `run_with_budget`
- [x] 5. Wire `harvesters` package into `pyproject.toml` ruff include and `.github/workflows/ci.yml` (lint + test-python matrix), with `harvesters/requirements.txt` / `requirements-dev.txt`
- [x] 6. Run `harvesters/tests` and confirm all pass; run `ruff check harvesters`
- [x] 7. Docs and contracts reviewed (spec/capabilities/harvester-framework.md delta applied at archive; no schema/ontology/harvester-interface change)
- [x] 8. `contract-check` and `secret-scan` run clean
- [x] 9. verification.md completed
