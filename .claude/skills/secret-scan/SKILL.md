---
name: secret-scan
description: Scan the working tree, diff, fixtures and logs for secrets (keys, tokens, passwords, connection strings) and confirm local secret files are untracked. Use before every commit and PR.
---

1. Confirm `.env` and other local secret files are git-ignored and untracked (`git ls-files | grep -E '\.env($|\.)'` should show only `.env.example`).
2. Search the diff and fixtures for patterns: private keys (`BEGIN .*PRIVATE KEY`), cloud keys (`AKIA`, `AIza`, service-account JSON with `private_key`), bearer tokens, `password=`, `secret=`, `api_key=`, connection strings with credentials, and high-entropy strings in config. Check fixtures and sample repos especially: demo data must be non-sensitive and contain no real credentials.
3. Check logs and test output for secret values.
4. Check `.env.example` contains names only.
5. If a secret is found: do not commit; remove it, rotate it, and tell the user. If it was already pushed, tell the user immediately; history must be cleaned and the key rotated.
6. Questions about access models, credential handling or data flows go to the Inspira security team at security@inspirafinancial.com.

Report: findings with file:line (never print the secret value), or "no secrets found".
