# Verification: KAN-80 Git harvest using the plan (sparse fetch)

Status: PASS

## Acceptance criteria

### 1. "fetches only planned paths"
- Scenario: excluded and oversize paths are never fetched.
- Evidence: `harvesters/tests/test_git_sparse_fetch.py::test_excluded_and_oversize_paths_are_never_fetched` — a repo with an included `src/App.java`, an excluded `target/App.class` and an oversize `big.sql` (2048 bytes, cap 1024) harvests only `src/App.java`; the other two are recorded `skipped` with reasons `"excluded by plan"` and `"exceeds size cap of 1024 bytes"`. `test_every_discovered_path_has_one_manifest_entry` additionally checks every discovered path is accounted for.
- Run: `python -m pytest harvesters/tests/test_git_sparse_fetch.py -q` → 5 passed.

### 2. "incremental by commit SHA"
- Scenario: incremental by commit SHA.
- Evidence: `test_incremental_by_commit_sha` — commit `A` has `a.sql`/`b.sql`; commit `B` changes only `a.sql`. Harvesting with `cursor=A` returns only `a.sql` as a `RawObject`; `b.sql` is recorded `skipped` with reason `"unchanged since cursor"`; `result.head_sha == B`.

### 3. "respects size caps"
- Scenario: size cap enforced.
- Evidence: `test_size_cap_enforced` — a 2048-byte file against `size_cap_bytes=1024` is skipped, reason contains `"size cap"`; a 3-byte file is fetched.

### 4. "writes manifest"
- Scenario: every discovered path has one manifest entry.
- Evidence: `test_every_discovered_path_has_one_manifest_entry` — `manifest.counts()["unaccounted"] == 0` and every `manifest.entries()` item has a non-empty `outcome` and `outcome_reason`, readable through the existing `Manifest.counts()`/`by_outcome()` API (KAN-77). Persisting the manifest via `ManifestStore` is exercised by KAN-77's own tests; this story only produces the in-memory `Manifest` the caller then saves.

### Budget behavior (named in the spec delta, not a separate Jira AC but part of "respects size caps"/plan enforcement)
- Evidence: `test_budget_stops_cleanly_and_leaves_remaining_unaccounted` — with `Budgets(max_files=1)` and two eligible files, exactly one is fetched, `result.budget_exceeded == "files"`, and the second stays in `manifest.unaccounted()`.

## Checks run
- `python -m pytest harvesters/tests -q` → 75 passed (full `harvesters` suite, including the 5 new tests).
- `python -m ruff check harvesters --config pyproject.toml` → All checks passed.
- `python scripts/spec_check.py spec/changes/kan-80-git-harvest-sparse-fetch` → `spec_check OK (plan)`.
- `python scripts/spec_check.py spec/changes/kan-80-git-harvest-sparse-fetch --stage=verify` → see below.
- contract-check (manual, per `.claude/skills/contract-check/SKILL.md` checklist): no schema/migration change; no new ontology types; `Harvester` interface signature unchanged (this story adds a plain function, not a registry-wired `Harvester` subclass, by design — see proposal "Out of scope"); no cloud SDK imports (`git grep` for `google.cloud`/`boto3`/`azure.` under `harvesters/git` → none); no MCP tool touched; `CLAUDE.md`/`docs/HARVESTERS.md` need no edit since the Git harvest *interface* is unchanged, only one source type's internal implementation of `harvest()` was added.
- secret-scan (manual, per `.claude/skills/secret-scan/SKILL.md` checklist): `git ls-files | grep -E '^\.env($|\.)'` → only `.env.example`; `grep -RniE "AKIA|BEGIN .*PRIVATE KEY|password=|api_key=|secret="` over the new files → no matches. Test fixtures are synthetic file contents created in a temp dir at test time, not checked-in fixture data, so no fixture secret-scan is needed.

## Not verified / deferred
- **Real remote Git hosts (HTTPS/SSH) and credentials.** Tests use local filesystem `file://`-style paths only (a plain local path, which `git clone` treats as a local transport). Partial-clone (`--filter=blob:none`) behavior against a real remote (GitHub, etc.) and `SecretStore`-backed auth are not exercised — `connect()` for Git (a separate, not-yet-started story) owns credentials.
- **Wiring into the `Harvester` registry / `get_harvester("git")`.** Deliberately out of scope (proposal "Out of scope"): `connect/discover/profile/plan/normalize/validate` for Git don't exist yet, so a full `GitHarvester` can't be assembled or registered yet. `harvest_git` is a standalone function a follow-up story will call from a `GitHarvester.harvest()` method.
- **Persisting the manifest and advancing `sources.last_cursor` in Postgres.** This story returns `GitHarvestResult.head_sha` and an in-memory `Manifest` for the caller (the future run-loop/dispatcher) to persist via the existing `ManifestStore`/`sources` update; no dispatcher integration exists yet to verify end-to-end.
- **`docker compose up` end-to-end.** Not run; this story has no new service, container, or compose entry — it is a pure-Python function added to an existing package with no new runtime dependency.
- **Non-ASCII / binary file content round-tripping through `git cat-file -p` + UTF-8 decode edge cases** beyond what the tests cover (test fixtures use UTF-8 text and short binary blobs); large binary files are expected to be filtered out upstream by the plan/size cap in real use per `docs/HARVESTERS.md`'s denylist-by-noise rule, which is a `plan()`-stage concern, not this story's.
