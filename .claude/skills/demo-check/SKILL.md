---
name: demo-check
description: Pre-demo readiness checklist. Use the day before and the hour before the hackathon demo.
---

Run and report PASS/FAIL per item; do not fix silently.

1. Clean start: `docker compose down -v && docker compose up` works from a fresh clone on the demo machine.
2. Seed data loaded through the real harvesters (`demo-data`); expected entities present (`fixtures/EXPECTED.md`).
3. UI: graph renders with seeded data; wizard flow works for Git and the SQL database; Run button produces a PUBLISHED run; a quarantined example is ready to show.
4. MCP: `search_context`, `get_related`, `get_lineage` return cited results.
5. Four demo agents run their scripted tasks; graph retrieval trace overlay works.
6. `eval-run` meets thresholds.
7. LLM endpoint reachable, credit balance sufficient, rate limits fine; fallback model or recorded responses ready if the endpoint fails.
8. `secret-scan` clean; `.env` untracked; demo uses synthetic data only.
9. GCP deploy (if shown): budget alert set, services healthy, teardown documented.
10. Backup plan: recorded video or screenshots, and the demo script (`CLAUDE.md` demo script and `DEMO_AGENTS.md`) open.
