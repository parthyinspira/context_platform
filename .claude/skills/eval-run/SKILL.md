---
name: eval-run
description: Run the golden questions and demo-agent tasks, report quality metrics and compare against the last baseline. Use after changing prompts, models, extraction, chunking or retrieval.
---

1. Load golden sets (retrieval questions and the four demo-agent task sets under the eval folder; follow the repo layout) and the fixture data expected entities (`fixtures/EXPECTED.md`).
2. Run against the current build (`docker compose up`, fixtures loaded).
3. Metrics: retrieval hit rate (expected source IDs present), citation coverage, hallucinated claim count (target 0), correct escalation rate, lineage accuracy (expected edges found, none invented), latency.
4. Compare to the stored baseline; list regressions and improvements with examples of the worst failures.
5. Fail (non-zero) below the thresholds in the eval config. Never raise a threshold or edit expected answers just to pass; if an expectation is wrong, explain and ask the user.
6. When the change is intentional, offer to update the baseline and record the model, prompt and embedding versions used.
