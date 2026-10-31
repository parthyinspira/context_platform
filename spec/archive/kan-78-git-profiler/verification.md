# Verification

Status: PASS
Date: 2026-10-31   Commit: d969ffa (merge of main's KAN-79/KAN-80 into this branch)

## Checks
| Check | Result |
|---|---|
| Lint (`ruff check harvesters/git`) | PASS — 0 errors |
| Lint (`ruff check api scheduler adapters ontology harvesters harvest_validation`) | 1 pre-existing error in `api/tests` (import order), unrelated to this change — confirmed present on `main` by stashing this change and re-running the same command |
| Tests (`python -m pytest harvesters -q`) | PASS — 115 passed (after merging KAN-79/KAN-80's new tests from `main`) |
| Tests (`python -m pytest harvesters/git/tests -q`) | PASS — 20 passed, reconciled against KAN-79's YAML rules and KAN-80's `harvest_git` |
| docker compose up exercised | Not applicable — this change adds no container/service; harvester packages are imported by other services, not run standalone |
| contract-check | No mismatches: no schema/ontology/MCP/adapter changes; harvester interface fully implemented (connect/discover/profile/plan/harvest real; normalize/validate explicitly deferred per the proposal's "Out of scope" with `NotImplementedError`); no cloud SDK imports outside `adapters/` |
| secret-scan | No secrets found in `harvesters/git/`; `.env` untracked, only `.env.example` tracked |
| Definition of Done | Tasks ticked in `tasks.md`; proposal, spec delta and this verification present |

## Reconciliation with parallel work
While this story was being built, KAN-79 (YAML stack rules) and KAN-80 (`harvest_git` sparse fetch) merged to `main`, both unaware of each other and of KAN-78 (each assumed `GitHarvester` connect/discover/profile/plan "not yet started"). Reconciled by merging `main` into this branch: `harvesters/git/stacks.py` now only detects stack names from markers (include/exclude/size-cap come from KAN-79's `harvesters/rules/*.yaml` via `load_stack_rules()`), `harvesters/git/__init__.py` exports both `GitHarvester` and KAN-80's `harvest_git`/`GitHarvestResult`, and `GitHarvester.harvest()` delegates to `harvest_git()`. See `proposal.md` "Changes during development" for detail. All pre-existing KAN-79/KAN-80 tests pass unchanged; `harvesters/git/tests/test_harvester.py` and `test_stacks.py` were updated for the `sql-dbt` -> `sql_dbt` rename and the new `harvest()` behavior.

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Discover without full clone / discover-lists-without-full-clone | `harvesters/git/tests/test_harvester.py::test_discover_lists_files_and_sizes_without_full_clone` | PASS |
| Discover without full clone / discover-no-blob-content-fetched | `harvesters/git/tests/test_harvester.py::test_discover_clone_uses_blob_none_filter_and_no_checkout` (asserts `--filter=blob:none` and `--no-checkout` on the actual `git clone` invocation) | PASS |
| Stack detection / detect-sql-dbt-stack | `harvesters/git/tests/test_stacks.py::test_detect_sql_dbt_stack`, `test_harvester.py::test_profile_detects_sql_dbt_stack` | PASS |
| Stack detection / detect-java-stack | `harvesters/git/tests/test_stacks.py::test_detect_java_stack`, `test_harvester.py::test_profile_detects_java_stack_and_excludes_target` | PASS |
| Stack detection / detect-dotnet-stack | `harvesters/git/tests/test_stacks.py::test_detect_dotnet_stack`, `test_harvester.py::test_profile_detects_dotnet_stack_and_excludes_bin_obj` | PASS |
| Stack detection / detect-talend-stack | `harvesters/git/tests/test_stacks.py::test_detect_talend_stack`, `test_harvester.py::test_profile_detects_talend_stack_and_excludes_screenshots_and_lib` | PASS |
| Stack detection / detect-shell-stack | `harvesters/git/tests/test_stacks.py::test_detect_shell_stack` | PASS |
| Profile with size estimates / profile-includes-size-estimates | `test_harvester.py::test_profile_detects_talend_stack_and_excludes_screenshots_and_lib`, `test_profile_estimate_totals_are_consistent` | PASS |
| Profile with size estimates / profile-estimate-excludes-denylisted-paths | `test_harvester.py::test_profile_detects_java_stack_and_excludes_target`, `test_profile_detects_dotnet_stack_and_excludes_bin_obj` | PASS |
| Plan from detected stacks / plan-includes-detected-stack-patterns | `test_harvester.py::test_plan_includes_detected_stack_patterns` | PASS |
| Harvest delegates to sparse fetch / harvest-fetches-planned-objects | `test_harvester.py::test_harvest_delegates_to_sparse_fetch` | PASS |
| Normalize and validate deferred / normalize-validate-not-yet-implemented | `test_harvester.py::test_normalize_validate_not_yet_implemented` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| 1. Lists files and sizes without full clone (`git ls-tree -l` / `filter=blob:none`) | discover-lists-without-full-clone, discover-no-blob-content-fetched | PASS |
| 2. Detects SQL, Java, .NET, Talend, shell | detect-sql-dbt-stack, detect-java-stack, detect-dotnet-stack, detect-talend-stack, detect-shell-stack | PASS |
| 3. Produces a profile with estimates | profile-includes-size-estimates, profile-estimate-excludes-denylisted-paths | PASS |

## Not verified
- `normalize()`/`validate()` for the git harvester are out of scope for this story (explicit `NotImplementedError`, see proposal); not a gap against KAN-78's AC. KAN-14's `normalize_repo()` exists as a standalone function but wiring it into `GitHarvester.normalize()` was not part of this reconciliation (KAN-14's own proposal defers that wiring to "other Epic 3 stories").
- Real remote git hosts (GitHub/GitLab/Azure DevOps/Bitbucket) were not exercised live; tests use local git repos built from `fixtures/repos/*` with `uploadpack.allowfilter=true` set explicitly, since that config defaults to disabled for local/file transports but is on by default for real hosts. The `git clone`/`ls-tree` commands used are identical either way.
- Shell-stack detection (`detect-shell-stack`) is covered by a unit test against path lists, not a dedicated fixture repository (no `fixtures/repos/*shell*` exists and adding one was out of scope per the proposal); `profile()`'s size-estimate path for the shell stack is therefore exercised only indirectly through `stacks.py` unit tests, not through a full discover+profile fixture run.
- The "docs" stack (`docs/HARVESTERS.md` section 4) has a YAML rules file (KAN-79) but no detection wired in `stacks.py`; explicitly called out as out of scope in `proposal.md` since it isn't named in KAN-78's AC.
- Windows vs. Linux: this session ran on Windows (git 2.50.1.windows.1); CI (`ubuntu-latest`) will run the same suite on Linux but that run has not completed as of this writing.
