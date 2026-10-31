# Delta for git-harvester

## ADDED Requirements

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
- **Then** `"sql-dbt"` is in the profile's detected stacks

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
The git harvester's `profile()` SHALL return a `GitProfile` (extending the shared `Profile`) carrying, per detected stack, an estimate of bytes that would be pulled under that stack's rules and an estimate of bytes that would be skipped as denylisted noise.

#### Scenario: profile-includes-size-estimates
- **Given** a discovered scope with files belonging to a detected stack
- **When** `profile()` is called
- **Then** the returned `GitProfile.estimated_pull_bytes_by_stack` holds a byte sum for that stack computed from the include patterns in `docs/HARVESTERS.md` section 4, and `GitProfile.estimated_skip_bytes` holds the byte sum of paths matching universal or stack denylist patterns (`.git`, `node_modules`, build output, binaries, media)

#### Scenario: profile-estimate-excludes-denylisted-paths
- **Given** a discovered scope containing both stack source files and denylisted paths (for example `target/`, `bin/`, `obj/`, `screenshots/`, `lib/`, or a file over the 1 MB size cap)
- **When** `profile()` is called
- **Then** the denylisted paths' bytes are counted in `estimated_skip_bytes`, not in any stack's `estimated_pull_bytes_by_stack`

### Requirement: Plan from detected stacks
The git harvester's `plan()` SHALL build a `HarvestPlan` whose include patterns come from the rules of every detected stack and whose exclude patterns include the universal denylist plus each detected stack's denylist, with a default 1 MB per-object size cap.

#### Scenario: plan-includes-detected-stack-patterns
- **Given** a `GitProfile` with `"sql-dbt"` detected
- **When** `plan()` is called
- **Then** the returned `HarvestPlan.include` contains the SQL/dbt stack's include patterns and `HarvestPlan.exclude` contains the universal denylist

### Requirement: Harvest, normalize and validate deferred
`harvest()`, `normalize()` and `validate()` on `GitHarvester` SHALL raise `NotImplementedError` naming the follow-up story, so the class remains instantiable without a half-built fetch or extraction path.

#### Scenario: harvest-not-yet-implemented
- **Given** a `GitHarvester` instance
- **When** `harvest()`, `normalize()` or `validate()` is called
- **Then** it raises `NotImplementedError` with a message naming the deferred scope
