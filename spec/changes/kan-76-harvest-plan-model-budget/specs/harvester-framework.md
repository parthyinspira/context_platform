# Delta for harvester-framework

## ADDED Requirements
### Requirement: Harvest plan model
A `HarvestPlan` SHALL hold include/exclude rules, a per-object size cap and budgets for files, bytes, wall time and tokens; exclude rules SHALL take precedence over include rules.

#### Scenario: include-exclude-precedence
- **Given** a plan with include pattern `*.sql` and exclude pattern `*/target/*`
- **When** a path matching both is checked
- **Then** the path is excluded

#### Scenario: plan-holds-caps-and-budgets
- **Given** a plan built with a size cap and budgets for files, bytes, time and tokens
- **When** the plan is read
- **Then** each value is present on the plan exactly as set

#### Scenario: default-plan-is-unrestricted
- **Given** a plan built with no arguments
- **When** a path is checked and the budgets are read
- **Then** the path is included and every budget dimension is unset (unlimited)
