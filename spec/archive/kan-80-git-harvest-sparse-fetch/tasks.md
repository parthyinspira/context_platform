# Tasks

- [x] 1. Write `harvesters/tests/test_git_sparse_fetch.py` with a helper that builds a real, synthetic local git repo (two commits) in a temp dir; cover: excluded/oversize paths never fetched, incremental by cursor SHA, size cap enforced, every path manifested, budget stops cleanly - test first (placed under `harvesters/tests/`, not `harvesters/git/tests/`, to match the CI invocation `pytest harvesters/tests`)
- [x] 2. Implement `harvesters/git/sparse_fetch.py`: `harvest_git(source, plan, cursor, manifest) -> GitHarvestResult` using a local partial bare clone, `git ls-tree -r -l`, `git diff --name-only` for incremental, `git cat-file -p` for blob content, `BudgetTracker` for budgets
- [x] 3. `harvesters/git/__init__.py` package scaffold
- [x] 4. Run `harvesters/git/tests` and confirm all pass; `ruff check harvesters/git` (no `pyproject.toml`/CI change needed: `harvesters/**/*.py` and `pytest harvesters/tests` already cover the new files)
- [x] 5. Docs and contracts reviewed (no schema/ontology/interface-signature change; capability delta applied at archive)
- [x] 6. `contract-check` and `secret-scan` run clean
- [x] 7. verification.md completed
