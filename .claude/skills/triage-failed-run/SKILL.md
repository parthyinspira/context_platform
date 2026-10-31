---
name: triage-failed-run
description: Investigate a FAILED or QUARANTINED harvest run from its state, manifest, validator report and logs, find the cause and propose a fix.
---

Input: a run id (or source id for the latest run).

1. Read the `harvest_runs` row: state, counts, plan, validation report. Identify the failing stage.
2. Read the manifest: fetched, skipped, failed objects with reasons. Look for budget hits, oversize files, parse failures, auth errors, rate limiting, delete spikes.
3. Read the validator report: which check failed and the sample failures.
4. Read logs for the run id; never print secret values.
5. Classify: source problem (credentials, permissions, source changed), plan/rules problem (too broad or too narrow), harvester bug, or expected quarantine (delete spike that is real).
6. Propose the smallest fix (rule change, plan edit, bug fix, credential rotation) and how to verify it with `harvest-dry-run`. Do not alter published knowledge or re-run against production without the user's approval.
7. If it is a defect, write it up as a Jira story draft for the user to file.
