# Tasks

- [x] 1. Write `harvesters/tests/test_stack_rules.py` (scenarios: stack-rules-loaded-per-stack, each-stack-plan-holds-size-cap, unknown-stack-raises, talend-fixture-plans-only-item-and-properties, plus per-stack fixture checks for sql_dbt/java/dotnet/shell/docs) - test first
- [x] 2. Add `harvesters/rules/{sql_dbt,java,dotnet,talend,shell,docs}.yaml` matching `docs/HARVESTERS.md` section 4
- [x] 3. Add `harvesters/framework/stack_rules.py`: `load_stack_rules`, `available_stacks`, `UnknownStackError`, `COMMON_EXCLUDE`
- [x] 4. Add `pyyaml` to `harvesters/requirements.txt`
- [x] 5. Run `harvesters/tests` and confirm all pass; run `ruff check harvesters`
- [x] 6. Spec delta applied: `spec/capabilities/harvester-framework.md` updated at archive time (delta in this folder's `specs/`)
- [x] 7. `contract-check` and `secret-scan` run clean
- [x] 8. `verification.md` completed
