# Capability: git harvester

### Requirement: Discover without full clone
The git harvester SHALL list files and sizes using a partial, blobless clone and `git ls-tree -l`, and SHALL NOT fetch blob content during discovery.

#### Scenario: discover-lists-without-full-clone
- **Given** a git source pointing at a fixture repository
- **When** `discover()` is called
- **Then** it returns a `ScopeTree` listing every tracked file with its path and byte size, read via `git ls-tree -r -l HEAD` against a clone created with `--filter=blob:none`

#### Scenario: discover-no-blob-content-fetched
- **Given** a git source pointing at a fixture repository
- **When** `discover()` is called
- **Then** the local clone used for discovery contains no fetched blob content (a blobless partial clone), only commit and tree objects

### Requirement: Stack detection
The git harvester SHALL detect the SQL/dbt, Java, .NET, Talend and shell/script stacks present in a repository from the marker files and extensions in `docs/HARVESTERS.md` section 4.

#### Scenario: detect-sql-dbt-stack
- **Given** a repository containing `dbt_project.yml` and `*.sql` files
- **When** `profile()` is called on its discovered scope
- **Then** `"sql_dbt"` is in the profile's detected stacks

#### Scenario: detect-java-stack
- **Given** a repository containing `pom.xml` and `src/main/java/**/*.java`
- **When** `profile()` is called on its discovered scope
- **Then** `"java"` is in the profile's detected stacks

#### Scenario: detect-dotnet-stack
- **Given** a repository containing a `.sln` file, a `.csproj` file and `*.cs` files
- **When** `profile()` is called on its discovered scope
- **Then** `"dotnet"` is in the profile's detected stacks

#### Scenario: detect-talend-stack
- **Given** a repository containing `talend.project` and `*.item`/`*.properties` job files
- **When** `profile()` is called on its discovered scope
- **Then** `"talend"` is in the profile's detected stacks

#### Scenario: detect-shell-stack
- **Given** a repository containing `*.sh` or `*.ps1` scripts
- **When** `profile()` is called on its discovered scope
- **Then** `"shell"` is in the profile's detected stacks

### Requirement: Profile with size estimates
The git harvester's `profile()` SHALL return a `GitProfile` (extending the shared `Profile`) carrying, per detected stack, an estimate of bytes that would be pulled under that stack's rules (loaded from `harvesters.framework.stack_rules.load_stack_rules`) and an estimate of bytes that would be skipped as denylisted noise.

#### Scenario: profile-includes-size-estimates
- **Given** a discovered scope with files belonging to a detected stack
- **When** `profile()` is called
- **Then** the returned `GitProfile.estimated_pull_bytes_by_stack` holds a byte sum for that stack computed from that stack's YAML rule include patterns (`harvesters/rules/<stack>.yaml`), and `GitProfile.estimated_skip_bytes` holds the byte sum of paths matching the universal or stack denylist patterns (`.git`, `node_modules`, build output, binaries, media) or over the per-stack size cap

#### Scenario: profile-estimate-excludes-denylisted-paths
- **Given** a discovered scope containing both stack source files and denylisted paths (for example `target/`, `bin/`, `obj/`, `screenshots/`, `lib/`, or a file over the 1 MB size cap)
- **When** `profile()` is called
- **Then** the denylisted paths' bytes are counted in `estimated_skip_bytes`, not in any stack's `estimated_pull_bytes_by_stack`

### Requirement: Plan from detected stacks
The git harvester's `plan()` SHALL build a `HarvestPlan` by merging the YAML rules (KAN-79, `load_stack_rules`) of every detected stack: include patterns from every detected stack's rule, exclude patterns from every detected stack's rule (each already includes the universal denylist), and the smallest per-stack size cap.

#### Scenario: plan-includes-detected-stack-patterns
- **Given** a `GitProfile` with `"sql_dbt"` detected
- **When** `plan()` is called
- **Then** the returned `HarvestPlan.include` contains the SQL/dbt stack's YAML include patterns and `HarvestPlan.exclude` contains the universal denylist

### Requirement: Harvest delegates to the sparse fetch
`GitHarvester.harvest()` SHALL delegate to `harvesters.git.sparse_fetch.harvest_git` (KAN-80), building a `Manifest` for the run from the source's id and a generated run id.

#### Scenario: harvest-fetches-planned-objects
- **Given** a `GitHarvester`, a plan built from a discovered and profiled fixture repository, and no cursor
- **When** `harvest()` is called
- **Then** it returns the `RawObject`s `harvest_git` fetched for the plan's included, under-cap paths

### Requirement: Normalize and validate deferred
`normalize()` and `validate()` on `GitHarvester` SHALL raise `NotImplementedError` naming the follow-up story, so the class remains instantiable without a half-built extraction or validation path.

#### Scenario: normalize-validate-not-yet-implemented
- **Given** a `GitHarvester` instance
- **When** `normalize()` or `validate()` is called
- **Then** it raises `NotImplementedError` with a message naming the deferred scope
