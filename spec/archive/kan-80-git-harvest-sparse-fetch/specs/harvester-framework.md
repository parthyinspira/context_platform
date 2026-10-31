# Delta for harvester-framework

## ADDED Requirements
### Requirement: Git sparse fetch
Given an approved `HarvestPlan` and a cursor, the Git harvest step SHALL fetch only paths the plan includes, under the plan's size cap, incrementally by commit SHA, and SHALL record every discovered path in a `Manifest` with a reason.

#### Scenario: excluded and oversize paths are never fetched
- **Given** a plan that excludes `target/*` and caps object size at 1 MB, and a repository containing an included small file, an excluded `target/` file and an included file over the cap
- **When** `harvest_git` runs with no cursor
- **Then** only the included, under-cap file is returned as a `RawObject`, and the excluded and oversize files are each recorded `skipped` in the manifest with a reason

#### Scenario: incremental by commit SHA
- **Given** a repository harvested once at commit `A`, then a second commit `B` that changes one file and leaves another untouched
- **When** `harvest_git` runs again with `cursor=A`
- **Then** only the file changed between `A` and `B` is returned as a `RawObject`, and the untouched file is recorded `skipped` with reason "unchanged since cursor"

#### Scenario: size cap enforced
- **Given** a plan with `size_cap_bytes=1024` and a repository file of 2048 bytes
- **When** `harvest_git` runs
- **Then** the file is not fetched and is recorded `skipped` with a reason naming the size cap

#### Scenario: every discovered path has one manifest entry
- **Given** a harvest run over a repository with included, excluded and oversize paths
- **When** the run completes
- **Then** every discovered path has exactly one outcome (`fetched` or `skipped`) with a non-empty reason, readable via `Manifest.counts()` and `Manifest.by_outcome()`

#### Scenario: budget stops the fetch cleanly
- **Given** a plan with `budgets.max_files=1` and two included, under-cap files
- **When** `harvest_git` runs
- **Then** exactly one `RawObject` is returned, the second file is left `unaccounted` in the manifest (discovered but no outcome), and the function reports which budget was hit
