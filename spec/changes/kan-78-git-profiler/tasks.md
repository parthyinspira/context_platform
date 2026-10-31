# Tasks

- [x] 1. `harvesters/git/stacks.py`: stack detection rules (markers, include/exclude globs) for sql-dbt, java, dotnet, talend, shell, plus the universal denylist (scenario: detect-sql-dbt-stack, detect-java-stack, detect-dotnet-stack, detect-talend-stack, detect-shell-stack) - test first
- [x] 2. `harvesters/git/harvester.py`: `connect()` via `git ls-remote` (no scenario named directly; covered by discover tests using the same fixture repos)
- [x] 3. `harvesters/git/harvester.py`: `discover()` via partial clone + `git ls-tree -r -l HEAD` (scenario: discover-lists-without-full-clone, discover-no-blob-content-fetched) - test first
- [x] 4. `harvesters/git/harvester.py`: `GitProfile` + `profile()` with per-stack size estimates (scenario: profile-includes-size-estimates, profile-estimate-excludes-denylisted-paths) - test first
- [x] 5. `harvesters/git/harvester.py`: `plan()` from detected stacks (scenario: plan-includes-detected-stack-patterns) - test first
- [x] 6. `harvesters/git/harvester.py`: `harvest()`/`normalize()`/`validate()` stubs (scenario: harvest-not-yet-implemented) - test first
- [x] 7. Register `GitHarvester` for source type `"git"` in `harvesters/__init__.py`
- [x] 8. Docs and contracts updated (none needed beyond the new capability spec; `docs/HARVESTERS.md` already documents this behaviour)
- [x] 9. verification.md completed
