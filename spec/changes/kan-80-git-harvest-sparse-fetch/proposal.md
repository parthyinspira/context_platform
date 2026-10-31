# KAN-80: Git harvest using the plan (sparse fetch)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-80   Epic: 3 Git harvester   Branch: kepler/kan-80-git-harvest-using-plan

## Why
`docs/HARVESTERS.md` section 4 ("Git") says: "Do not clone fully. Use `git clone --filter=blob:none --sparse` (partial clone)... to get sizes first, then fetch only the planned paths." No Git-specific harvester code exists yet (only the shared framework: `Harvester` base class (KAN-12/KAN-75), `HarvestPlan`/`Budgets` (KAN-76), `Manifest` (KAN-77)). This story is the `harvest()` step named directly in the Jira summary: given an *already-approved* `HarvestPlan` and a cursor, fetch only the planned Git paths, incrementally by commit SHA, under the plan's size cap, and write a manifest. `connect`, `discover`, `profile` and `plan` for Git are separate, not-yet-started stories.

## What changes
- New package `harvesters/git/` with `sparse_fetch.py`: a `harvest_git(source, plan, cursor, manifest) -> GitHarvestResult` function (not a full `Harvester` subclass — see Out of scope).
- Uses a local **partial bare clone** (`git clone --bare --filter=blob:none <uri> <tmp>`) so blob content is never downloaded for excluded paths — the "sparse fetch" from `docs/HARVESTERS.md`.
- Lists the tree at the target ref with `git ls-tree -r -l` (names + sizes, no blob fetch), filters by `plan.is_included(path)` and `plan.size_cap_bytes`.
- Incremental: when `cursor` (a commit SHA) is given, only paths that changed between `cursor` and the target commit (`git diff --name-only`) are fetched; unchanged paths are recorded as `skipped` with reason `"unchanged since cursor"`. No cursor means every included, under-cap path at the target commit is fetched.
- For each accepted path, fetches the blob on demand (`git cat-file -p <sha>:<path>`) and yields a `RawObject`.
- Every discovered path gets a `Manifest` entry; excluded paths, oversize paths and unchanged (incremental skip) paths are recorded `skipped` with a reason; fetched paths are recorded `fetched`. The caller (not this story) persists the manifest via `ManifestStore` and advances `sources.last_cursor`.
- New result type `GitHarvestResult(objects: list[RawObject], head_sha: str)` so the caller can read the new cursor to persist.
- Budgets (`plan.budgets`) are enforced with the existing `harvesters.framework.budget.BudgetTracker`; hitting one stops the fetch loop cleanly (remaining discovered-but-not-yet-fetched paths stay `unaccounted` in the manifest, matching KAN-76/83's `PARTIAL` semantics — marking `harvest_runs.state = PARTIAL` is the dispatcher/run-loop's job, out of scope here).
- Tests use a real local Git repository built from `fixtures/repos/java-sample` (plus `target/` files) as the fixture source, so partial clone and sparse-fetch behavior is exercised against real `git` rather than mocked.

## In scope
- `harvesters/git/__init__.py`, `harvesters/git/sparse_fetch.py`, `harvesters/git/requirements*.txt` (if git pack needs its own deps — none expected, stdlib `subprocess` only).
- `harvesters/tests/test_git_sparse_fetch.py` (or `harvesters/git/tests/`), including a fixture helper that turns a plain fixture directory into a real git repo with two commits (to test incremental-by-SHA).
- Spec delta: new requirement "Git sparse fetch" under `spec/capabilities/harvester-framework.md`.
- Wiring into `pyproject.toml` ruff include / CI matrix only if `harvesters/git` needs a separate entry (it is already under `harvesters/`, so likely none needed — verified in develop).

## Out of scope
- `GitHarvester.connect/discover/profile/plan/normalize/validate` and registering `"git"` in the harvester registry — separate stories; this story is exactly the "harvest" step named in the Jira summary.
- Remote (non-local-filesystem) Git hosts, authentication, SSH/HTTPS credential handling — `SecretStore`-backed credentials are a `connect()`-stage concern (out of scope).
- Writing to `harvest_runs` / advancing `sources.last_cursor` in Postgres, and the dispatcher's `PARTIAL` run-state transition — those belong to the run-loop/dispatcher (Epic 4), not the harvest function itself.
- `normalize()` (turning `RawObject`s into entities/edges) — a separate story.
- Secret/PII redaction of fetched file *content* — `adapters.scanning.scan_and_redact` is applied at chunk-write time (per `spec/capabilities/harvester-framework.md` "Read-only and secret-safe", already implemented); this story only scans manifest *reasons*, which `Manifest.discovered/fetched/skipped/failed` already redacts.

## Acceptance criteria (from Jira)
1. "fetches only planned paths" -> scenario: plan-excluded and oversize paths are never fetched, only recorded skipped
2. "incremental by commit SHA" -> scenario: a second harvest with `cursor=<first head sha>` only fetches paths changed since that commit
3. "respects size caps" -> scenario: a path over `plan.size_cap_bytes` is skipped with reason naming the cap
4. "writes manifest" -> scenario: every discovered path has exactly one manifest entry (fetched or skipped) with a reason, and the manifest is readable via `Manifest.counts()` / `by_outcome()`

## Affected
Capabilities: `spec/capabilities/harvester-framework.md` (ADDED requirement "Git sparse fetch"). Docs: no contract/interface signature change (the `Harvester.harvest()` signature in `CLAUDE.md`/`docs/HARVESTERS.md` is unchanged; this is one source-type's internal implementation of it). No Postgres schema, ontology or Confluence Contracts change.

## Risks and open questions
- Partial clone (`--filter=blob:none`) over the local filesystem transport needs a recent `git` (2.36+ reliably supports file-transport partial clone); verified against the repo's installed `git` in develop/verify.
- This function is deliberately not wired into the `Harvester` registry (`get_harvester("git")` still raises `UnknownSourceTypeError`) since `connect/discover/profile/plan` don't exist yet; a follow-up story assembles `GitHarvester` from this plus those pieces.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
