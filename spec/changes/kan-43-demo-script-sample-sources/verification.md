# KAN-43 Verification

| AC | Scenario | Result | Evidence |
|---|---|---|---|
| 1. Non-sensitive fixtures | All fixture text files scanned for unlabeled real secrets | PASS | `test_demo_fixtures.py::test_no_real_secrets` passes (9/9 tests green); Talend fake secret is labeled `FAKE_API_KEY` with comment "clearly fake, fixture for redaction tests" |
| 1. Non-sensitive fixtures | Fixture repos and docs match EXPECTED.md entries | PASS | `test_expected_md_repos_match_disk` and `test_expected_md_docs_match_disk` pass |
| 2. Script end to end | demo/demo.sh covers all 4 CLAUDE.md demo steps | PASS | Step 1: POST /sources (git); Step 2: poll run to PUBLISHED; Step 3: MCP search_context; Step 4: upload doc + search; script exits 0 on all steps |
| 2. Script end to end | demo/README.md documents prerequisites and expected output | PASS | README covers prerequisites, per-step expected output, fixture table, and troubleshooting |

## Not verified here
- Actual harvester run completing to PUBLISHED (requires running compose stack; covered by KAN-101 compose tests and manual demo rehearsal).
- MCP search_context returning correct citations (requires live embeddings service).

## spec_check
```
spec_check OK (lite plan): spec/changes/kan-43-demo-script-sample-sources
```

## Tests
```
9 passed in 0.70s
```
