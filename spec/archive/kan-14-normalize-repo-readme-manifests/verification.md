# Verification: KAN-14

Status: PASS

## Acceptance criterion
"Creates Repository, Module, Person/Team entities and OWNED_BY/DEPENDS_ON edges deterministically."

## Evidence per scenario

| Scenario | Test | Result |
|---|---|---|
| repository-from-readme | `test_repository_from_readme`, `test_repository_without_readme_has_no_description` | PASS |
| module-and-dependency-from-package-json | `test_module_and_dependency_from_package_json` | PASS |
| module-and-dependency-from-pom-xml | `test_module_and_dependency_from_pom_xml` | PASS |
| module-and-dependency-from-csproj | `test_module_and_dependency_from_csproj` | PASS |
| repo-level-dependency-from-requirements-txt | `test_repo_level_dependency_from_requirements_txt` | PASS |
| person-and-team-from-codeowners | `test_parse_codeowners`, `test_classify_owner`, `test_person_and_team_from_codeowners` | PASS |
| combined-normalize-repo | `test_combined_normalize_repo` | PASS |
| no-llm-call (deterministic) | `test_normalize_repo_is_deterministic` | PASS |

```
$ python -m pytest harvesters/tests/test_git_normalize.py -q
...........
11 passed in 0.42s

$ python -m pytest harvesters/tests -q
........................................................................ [ 88%]
.........                                                                [100%]
81 passed in 0.30s

$ ruff check harvesters --config pyproject.toml
All checks passed!
```

## contract-check
No mismatches: `Repository`, `Module`, `Person`, `Team`, `OWNED_BY`, `DEPENDS_ON` all already exist in CLAUDE.md's Ontology v0 list (no new types added, nothing routed through `proposed_changes`). No Postgres schema change, no migration needed. No cloud SDK imports introduced. `harvesters/git/normalize.py` is a standalone extraction module (not a full `Harvester` subclass) by design — see proposal.md "Out of scope" (no `GitHarvester.connect/discover/harvest` exists yet in this repo); this mirrors the KAN-25 SQL lineage precedent.

## secret-scan
No secret-shaped values in `harvesters/git/fixtures/` or `harvesters/git/normalize.py`. `.env` remains untracked (`git ls-files | grep -E '\.env($|\.)'` shows only `.env.example`).

## Not verified / known gaps (called out per proposal.md "Out of scope")
- **Not wired into a real Git harvester.** No `GitHarvester` with `connect`/`discover`/`harvest` exists in this repo yet (tracked by other Epic 3 stories); `normalize_repo()` is a function a future `GitHarvester.normalize()` will call.
- **CODEOWNERS ownership is repository-level only**, not resolved to the specific Module a CODEOWNERS glob pattern covers — a future harvester has real file paths to do that matching; this story emits `OWNED_BY` from the `Repository` entity for every distinct owner.
- **No persistence.** Entities/edges are returned as Python values; no Postgres write path exists for Git-sourced entities yet.
- **No new `fixtures/repos/*` tree.** This story's fixtures live under `harvesters/git/fixtures/` (unit-test fixtures), not the `fixtures/` capability owned by KAN-88; adding README/manifest/CODEOWNERS content to the shared sample repos is separate follow-up work, not bundled here.
- **Dependency version/lockfile resolution is out of scope** — only directly declared manifest dependencies by name.
