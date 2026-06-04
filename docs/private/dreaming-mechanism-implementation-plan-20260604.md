# Hermes Dreaming Mechanism Implementation Plan — 2026-06-04

Goal: advance Hermes dreaming/nightly autonomous evolution from cron-success scripts to proof-backed canonical-state consolidation, stopping only at explicit human-intervention gates.
Status: implemented_pending_commit
SSOT: /Users/charles/.hermes/docs/private/dreaming-mechanism-theory-and-architecture-20260604.md

## Constraints
- archived data sources are read-only; never write under ~/.hermes/skills-archived/.
- success means effective state advancement or explicit advisory/no-op proof, not cron exit 0.
- no stealth / Cloudflare bypass; no Scrapling as core dependency.
- keep changes scoped; avoid staging unrelated pre-existing dirty files.
- local scripts impact: run py_compile and focused tests.

## Steps
- [x] Step 0: Create theory/architecture SSOT — /Users/charles/.hermes/docs/private/dreaming-mechanism-theory-and-architecture-20260604.md
- [x] Step 1: Create implementation plan and inspect Hermes local constitution / current script baseline.
- [x] Step 2: Add RED tests for canonical Dream/Evolution store behavior: archived read-only, canonical write path, effective health.
- [x] Step 3: Implement minimal dream/evolution state store + optional archived import helper.
- [x] Step 4: Integrate no-agent nightly wrapper with effective health parsing and canonical run ledger.
- [x] Step 5: Integrate autonomous-evolution-nightly.py data-path resolution with canonical writable store where safe.
- [x] Step 6: Run focused verification and mocked no-agent smoke run.
- [ ] Step 7: Scoped git commit of only this request's files.

## Decisions
- Use ~/.hermes/state/dreaming/ as Dream run/proof ledger root.
- Use ~/.hermes/state/evolution/ as writable canonical evolution data root for confidence-db/results compatibility.
- Keep archived as import/read-only source only.
- First landing should be low-risk local scripts + tests, not Hermes core runtime rewrite.

## Files Changed
- /Users/charles/.hermes/docs/private/dreaming-mechanism-theory-and-architecture-20260604.md
- /Users/charles/.hermes/docs/private/dreaming-mechanism-implementation-plan-20260604.md
- /Users/charles/.hermes/scripts/hermes_evolution_store.py
- /Users/charles/.hermes/scripts/test_hermes_evolution_store.py
- /Users/charles/.hermes/scripts/autonomous-evolution-nightly.py
- /Users/charles/.hermes/scripts/autonomous_evolution_nightly_noagent.py
- /Users/charles/.hermes/scripts/refresh-dashboard.py

## Verification
- cd ~/.hermes/scripts && /Users/charles/.hermes/hermes-agent/.venv/bin/python -m pytest test_hermes_evolution_store.py -q
- python3 -m py_compile ~/.hermes/scripts/hermes_evolution_store.py ~/.hermes/scripts/autonomous-evolution-nightly.py ~/.hermes/scripts/autonomous_evolution_nightly_noagent.py ~/.hermes/scripts/refresh-dashboard.py ~/.hermes/scripts/test_hermes_evolution_store.py
- git -C ~/.hermes diff --check -- <scoped changed files>
