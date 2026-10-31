# 3-day plan: demo-critical path

Deadline: 3 days. The demo shows one thing end to end: add a Git repo in the UI, approve the harvest plan, harvest and validate it, see the knowledge graph, and have one agent answer a lineage question with citations. Everything else is stretch.

## Demo-critical bundles (about 48 stories, 12 runs)
Each bundle is one `spec-batch` run (one plan approval, one PR). "Minimal" means the simplest version that satisfies the acceptance criteria.

| Bundle | Stories (KAN) | Notes |
|---|---|---|
| B1 Foundation | 4, 102, 5 | KAN-101 done. KAN-5 includes the Ubuntu CI job that runs `docker compose up` |
| B2 Sources API | 7, 8, 9, 10, 106 | API plus event plus run endpoint |
| B3 UI shell | 57, 59, 60 | Parallel with B2 |
| B4 Harvest core | 75, 12, 76, 77, 85 | Interface, `harvest_runs`, plan and budgets, manifest, publish gate |
| B5 Git harvest | 78, 79, 80, 14, 82, 16 | Profiler, stack rules, plan-driven harvest, normalize, secret scan, job container |
| B6 Validator | 83, 84 | Minimal checks: completeness, exclusion integrity, budgets, secrets, delete sanity. Parallel with B5 |
| B7 Knowledge store | 15, 19, 20, 24, 25, 29 | Chunks and embeddings, upserts, tombstones, ontology v0, SQL lineage (sqlglot), ontology updater (deterministic only) |
| B8 UI wizard and runs | 58, 61, 62, 63, 64, 65 | Minimal wizard, run view and report |
| B9 Graph UI | 66, 68 | Canvas plus inspector (filters 67 are stretch) |
| B10 Retrieval MCP | 31, 32, 33, 48 | Context service, `search_context`, `get_related`, `get_lineage` |
| B11 Agent | 88, 98, 93, 94 | Fixtures, seeded demo data, grounding module, one agent: workflow change-impact (shows lineage) |
| B12 Demo | 100, 43 | Demo script and rehearsal |

## Schedule
- **Day 1:** B1 + B2 + B3 in parallel; start B4 and B6; pure-Python pieces (82, 24, 25, 88) alongside.
- **Day 2:** B5 + B7, B8, B10.
- **Day 3 morning:** B9, B11. **Day 3 afternoon:** B12, rehearsal, fixes. Freeze before the demo.

## Cut line (if time runs short, cut from the bottom)
1. Agent grounding works on the CLI before the UI polish.
2. Graph shows entities from Git manifests and SQL lineage; skip layout tuning.
3. Wizard stays minimal; skip editable rules in the plan preview.
4. Keep the validator to the minimal checks.

## Stretch (only if time is left)
72 agents screen with retrieval trace overlay; 67 graph filters; 34 token budgets; 95/96/97 other agents; 81 SQL database harvester; 37 to 39 uploads; 21/107 retries and alerts; 22 webhook; 26 to 28 LLM extraction and entity resolution; 35, 46, 47, 49 to 55 more MCP; 69 to 71 graph polish; 86 to 91 pack tooling and stubs; 41/42/99 evals; 108 GCP deploy; 44 docs; 73 design review.

Needs you: KAN-103 (Llama key in `.env`) before any LLM-dependent story (only the agent in B11 needs one).

Jira filter for the critical path:
`project = KAN AND key in (KAN-4,KAN-102,KAN-5,KAN-7,KAN-8,KAN-9,KAN-10,KAN-106,KAN-57,KAN-59,KAN-60,KAN-75,KAN-12,KAN-76,KAN-77,KAN-85,KAN-78,KAN-79,KAN-80,KAN-14,KAN-82,KAN-16,KAN-83,KAN-84,KAN-15,KAN-19,KAN-20,KAN-24,KAN-25,KAN-29,KAN-58,KAN-61,KAN-62,KAN-63,KAN-64,KAN-65,KAN-66,KAN-68,KAN-31,KAN-32,KAN-33,KAN-48,KAN-88,KAN-98,KAN-93,KAN-94,KAN-100,KAN-43)`
