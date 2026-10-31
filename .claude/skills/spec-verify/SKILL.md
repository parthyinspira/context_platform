---
name: spec-verify
description: Stage 3 of spec-driven development. Use when all tasks are done to prove the change meets every scenario and acceptance criterion and write verification.md.
---

Follow `spec/workflow/03-verify.md`. In lite mode (`spec/workflow/07-lite.md`) keep it short: unit tests and `secret-scan` per story, and run Docker and `contract-check` once per bundle. Run lint and the full test suite, exercise the change with `docker compose up`, run the `contract-check` skill, and fill `verification.md` from `spec/templates/verification.md` with evidence per scenario and per acceptance criterion. Run `python scripts/spec_check.py <change-folder> --stage=verify`.

Set Status to PASS only if everything is evidenced; otherwise FAIL with reasons and return to `spec-develop`. Mark anything you could not verify as NOT VERIFIED with the reason. Do not open a PR in this stage.
