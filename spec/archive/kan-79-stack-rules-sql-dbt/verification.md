# Verification

Status: PASS
Date: 2026-10-31   Commit: bedd85f

## Checks
| Check | Result |
|---|---|
| Lint (`ruff check harvesters --config pyproject.toml`) | PASS, no findings |
| Tests (`python -m pytest harvesters/tests -q`) | PASS, 79 passed |
| docker compose up exercised | Not applicable — pure in-memory rule loader, no service, no compose change |
| contract-check | No mismatches: no schema/ontology/harvester-interface/adapter/MCP change; `docs/HARVESTERS.md` section 4 already documented this table and the new rules match it exactly |
| secret-scan | No secrets found in new files; `.env.example` is the only tracked `.env*` file |
| Definition of Done | Tests first, within proposal scope, spec delta added, requirement added to `spec/capabilities/harvester-framework.md` at archive |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command) | Result |
|---|---|---|
| Stack rules / stack-rules-loaded-per-stack | `harvesters/tests/test_stack_rules.py::test_available_stacks_lists_all_six`, `::test_each_stack_returns_a_harvest_plan_with_size_cap`, `::test_java_fixture_excludes_target_and_includes_source_and_build_files`, `::test_dotnet_fixture_excludes_bin_and_obj_and_includes_source_and_config`, `::test_sql_dbt_fixture_includes_models_and_schema`, `::test_shell_rule_includes_scripts_and_excludes_logs`, `::test_docs_rule_includes_markdown_and_readme_and_excludes_images` | PASS |
| Stack rules / each-stack-plan-holds-size-cap | `harvesters/tests/test_stack_rules.py::test_each_stack_returns_a_harvest_plan_with_size_cap` | PASS |
| Stack rules / unknown-stack-raises | `harvesters/tests/test_stack_rules.py::test_unknown_stack_raises` | PASS |
| Stack rules / talend-fixture-plans-only-item-and-properties | `harvesters/tests/test_stack_rules.py::test_talend_fixture_plans_only_item_and_properties_files` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| 1. YAML rules per stack with include/exclude and caps | stack-rules-loaded-per-stack, each-stack-plan-holds-size-cap, unknown-stack-raises | PASS — `harvesters/rules/{sql_dbt,java,dotnet,talend,shell,docs}.yaml` each hold `include`/`exclude` globs and `size_cap_bytes`; `load_stack_rules` turns them into a `HarvestPlan` |
| 2. Fixture tests prove a Talend-like repo plans only .item/.properties files | talend-fixture-plans-only-item-and-properties | PASS — `test_talend_fixture_plans_only_item_and_properties_files` walks every file under `fixtures/repos/talend-sample/` and asserts the included set is exactly `{jobs/load_orders.item, jobs/load_orders.properties}` |

## Not verified
- Use by a real Git harvester's `plan()` step: no Git harvester exists yet in this repo (Epic 3 not built), so `load_stack_rules` has no production call site beyond its own tests and the fixture repos — by design, per the proposal's "Out of scope" section, matching the precedent set by `spec/archive/kan-76-harvest-plan-model-budget`.
- Stack *detection* from marker files (`pom.xml`, `*.sln`, `talend.project`, etc.): out of scope for this story; these rules assume the stack is already known.
- Full-repo `python -m pytest` (all packages at once) was not run: the repo's root conftest setup causes a pre-existing module-name collision between `api/tests/test_health.py` and `scheduler/tests/test_health.py` unrelated to this change (CI runs tests per-package via a matrix, which is what was used here: `python -m pytest harvesters/tests -q`).
