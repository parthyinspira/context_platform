# KAN-78: Git profiler: partial clone, size listing, stack detection

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-78   Epic: 3 Git harvester   Branch: kan-78-git-profiler-partial-clone

## Why
Epic 3 needs the git harvester's discovery and profiling slice before plan/harvest/normalize can be built on top of it. Per `docs/HARVESTERS.md` section 4 ("Git"), a git source must never be fully cloned: files and sizes are listed with `git ls-tree -l` against a partial clone (`--filter=blob:none`), and the detected stack (SQL/dbt, Java, .NET, Talend, shell) drives what a later plan will pull. Today `harvesters/` has only the generic framework (KAN-75/76/77); no concrete source-type harvester exists yet.

**Reconciled with parallel work (changed during development):** while this story was in flight, KAN-79 (YAML per-stack rules, `harvesters/framework/stack_rules.py` + `harvesters/rules/*.yaml`) and KAN-80 (`harvesters/git/sparse_fetch.py`'s `harvest_git()`, the actual sparse-fetch `harvest()` step) merged to `main` in parallel, built against the assumption that connect/discover/profile/plan did not exist yet. This story now builds `GitHarvester` as the thing that ties those two together: stack *detection* (markers -> stack names) here, include/exclude/size-cap rules loaded from KAN-79's YAML files (no second copy of the rules), and `harvest()` delegating to KAN-80's `harvest_git()`.

## What changes
- Add `harvesters/git/` package: a `GitHarvester` registered for source type `"git"` in the plugin registry, alongside the existing `harvesters/git/sparse_fetch.py` (KAN-80).
- `connect()`: verifies read access with `git ls-remote`, no clone.
- `discover()`: creates a partial, blobless clone (`git clone --filter=blob:none --sparse --no-checkout`) and lists every file with `git ls-tree -r -l HEAD`, returning a `ScopeTree` of paths and sizes. No blob content is fetched.
- `profile()`: detects stacks (SQL/dbt, Java, .NET, Talend, shell) from marker files per the table in `docs/HARVESTERS.md`, using KAN-79's `load_stack_rules()` for each detected stack's include/exclude/size cap, and returns a `GitProfile` (extends the shared `Profile`) with object/byte totals, counts by stack, and a per-stack estimate of bytes that would be pulled vs. skipped.
- `plan()`: builds a `HarvestPlan` by merging the detected stacks' YAML rules (KAN-79), reusing the shared `HarvestPlan`/`Budgets` model. No budgets are set in this story (left for a later story to tune).
- `harvest()`: delegates to KAN-80's `harvest_git()`, building a `Manifest` for the run.
- `normalize()` and `validate()` are explicitly out of scope for this story (see below) and raise `NotImplementedError` naming the follow-up story, so the class is instantiable (satisfies the ABC) without half-built extraction/validation logic.

## In scope
- Partial clone + `git ls-tree -l` based discovery (no full clone, no blob content fetched).
- Stack detection for SQL/dbt, Java, .NET, Talend, shell/scripts, using the marker files in `docs/HARVESTERS.md` section 4; rule content (include/exclude/size cap) is loaded from KAN-79's YAML files, not duplicated.
- A profile with size estimates (bytes likely to be pulled per detected stack vs. skipped) built from the existing fixtures (`fixtures/repos/sql-dbt-sample`, `java-sample`, `dotnet-sample`, `talend-sample`).
- `plan()` built deterministically by merging the detected stacks' YAML rules.
- `harvest()` wired to KAN-80's `harvest_git()` so `GitHarvester` is a complete, usable connect->discover->profile->plan->harvest harvester (normalize/validate pending).

## Out of scope
- `normalize()` (entity/edge extraction) and `validate()` — tracked for a follow-up Epic 3 story; stubbed to raise `NotImplementedError`.
- The "docs" stack (`README*`/`docs/**`/`*.md`) from `docs/HARVESTERS.md` section 4 — a YAML rules file exists (KAN-79, `harvesters/rules/docs.yaml`) but detecting it is not named in this story's AC (SQL, Java, .NET, Talend, shell only); a follow-up can add detection for it.
- Incremental/cursor plumbing beyond what `harvest_git()` already does (commit-SHA cursoring) — owned by KAN-80.
- CODEOWNERS-based Person/Team extraction — part of `normalize()`, out of scope here.
- New fixtures — this story reuses the existing fixture repos; it does not add a shell-script fixture (stack detection is covered by marker-file unit tests, not a new fixture directory).
- UI wiring (Add-source wizard discover/profile screens) — not named in the AC.

## Acceptance criteria (from Jira)
1. Lists files and sizes without full clone (`git ls-tree -l` / `filter=blob:none`) -> scenarios: discover-lists-without-full-clone, discover-no-blob-content-fetched
2. Detects SQL, Java, .NET, Talend, shell -> scenarios: detect-sql-dbt-stack, detect-java-stack, detect-dotnet-stack, detect-talend-stack, detect-shell-stack
3. Produces a profile with estimates -> scenarios: profile-includes-size-estimates, profile-estimate-excludes-denylisted-paths

## Affected
Capabilities: `spec/capabilities/git-harvester.md` (new)   Docs/contracts: none (no schema/ontology/harvester-interface change; `docs/HARVESTERS.md` section 4 already documents this behaviour, this story implements it)

## Risks and open questions
- `git clone --filter=blob:none` over the local `file://` transport requires `uploadpack.allowFilter=true` on the source repo; real remote git hosts (GitHub/GitLab/Azure DevOps/Bitbucket) enable this by default, but tests build local bare repos from the fixtures and must set this config explicitly to exercise the real partial-clone path.
- "Estimates" in the AC has no numeric precision requirement; this story defines it as a per-stack byte sum of `ls-tree` sizes for included paths vs. excluded paths, which is deterministic and testable without fetching content.

## Changes during development
- Reconciled with KAN-79 (YAML stack rules) and KAN-80 (`harvest_git()` sparse fetch), which merged to `main` in parallel with this story and both touch git-harvester territory. Rewrote `harvesters/git/stacks.py` to only detect stack names from markers (dropped the originally hardcoded include/exclude patterns, now loaded from KAN-79's `harvesters/rules/*.yaml` via `load_stack_rules()`), renamed the `sql-dbt` stack identifier to `sql_dbt` to match KAN-79's file naming, resolved an add/add conflict on `harvesters/git/__init__.py` so it exports both `GitHarvester` and KAN-80's `harvest_git`/`GitHarvestResult`, and wired `GitHarvester.harvest()` to call `harvest_git()` instead of raising `NotImplementedError` (narrowing this story's "out of scope" to normalize/validate only). See the PR for the reconciliation commit.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31
