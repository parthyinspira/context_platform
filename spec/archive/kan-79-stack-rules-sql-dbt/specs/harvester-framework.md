# Delta for harvester-framework

## ADDED Requirements
### Requirement: Stack rules
The project SHALL provide deterministic include/exclude glob rules and a per-object size cap, as a `HarvestPlan`, for each stack named in `docs/HARVESTERS.md` section 4 (SQL/dbt, Java, .NET, Talend, shell/scripts, docs), loaded from YAML files under `harvesters/rules/` by `harvesters.framework.stack_rules.load_stack_rules(stack)`.

#### Scenario: stack-rules-loaded-per-stack
- **Given** the six stacks named in `docs/HARVESTERS.md` section 4
- **When** `load_stack_rules(stack)` is called for each
- **Then** it returns a `HarvestPlan` whose include patterns match the stack's documented "pull" column and whose `is_included` check rejects paths matching the stack's documented "skip" column

#### Scenario: each-stack-plan-holds-size-cap
- **Given** a stack's loaded `HarvestPlan`
- **When** `size_cap_bytes` is read
- **Then** it is set to the default per-object cap documented in `docs/HARVESTERS.md` rule 4

#### Scenario: unknown-stack-raises
- **Given** a stack name with no rules file under `harvesters/rules/`
- **When** `load_stack_rules(stack)` is called
- **Then** it raises `UnknownStackError` naming the unknown stack

#### Scenario: talend-fixture-plans-only-item-and-properties
- **Given** the Talend stack rules and every file path under `fixtures/repos/talend-sample/`
- **When** each path is checked against the loaded plan
- **Then** only `jobs/load_orders.item` and `jobs/load_orders.properties` are included; the jar, screenshot, project marker and README are all excluded
