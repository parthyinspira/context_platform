# Milestones: build in batches, not one story at a time

Each milestone is built on one branch (`m<n>-<slug>`) with one commit group per Jira story, one combined plan approval, and one PR. Each milestone ends with something you can run.

| M | Name | Stories (KAN) | You can then |
|---|---|---|---|
| M1 | Walking skeleton | 101 compose stack, 102 adapters, 104 embedding container, 4 schema + migrations, 5 repo skeleton + CI, 7/8 sources API, 9 event, 10 credential ref, 106 dispatcher run endpoint, 57 UI skeleton, 59 components, 60 Sources screen | `docker compose up`, open the UI, add a source row, press Run (stub), see the run state |
| M2 | Git end to end | 75 interface + harvest_runs, 76 plan + budgets, 77 manifest, 12 base class, 78 Git profiler, 79 stack rules, 80 plan-driven Git harvest, 14 normalize repo, 15 chunk + embed, 16 job container, 82 secret scan, 83/84 validator, 85 publish gate, 19/20 upserts + tombstones, 24/25/29 ontology, 58 UI API, 61 to 65 wizard, run view, report, 66 to 68 graph | Add a Git repo in the UI, approve the plan, run, see the knowledge graph |
| M3 | More sources + MCP | 81 SQL database, 88 fixtures, 37 to 39 uploads, 26 to 28 LLM extraction and resolution, 31 to 35 context service + MCP tools, 47 to 51 more MCP tools + auth, 86 pack structure, 21 retries, 107 alerts, 69 to 71 graph polish | Add a database and documents; query through MCP |
| M4 | Agents + demo | 93 to 100 demo agents, 72 agents screen, 46/50/52 MCP servers, 41/42/43 evals + demo script, 108 GCP deploy, 44 docs | Run the four agents, rehearse the demo |

Items that need you: KAN-103 (Llama endpoint and key in `.env`), a running Docker Desktop with WSL2 for M1 verification, GCP login for KAN-108.

Order inside a milestone follows dependencies (schema and adapters before APIs, APIs before UI).
