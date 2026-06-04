# Hermes dirty-state ranked execution plan — 2026-06-04

Decision: approve B+D hybrid from multi-model round. Proceed with read-only deep inventories, then scripts/** diff clustering before any semantic commit. No broad cleanup/ignore/reset is authorized by this document.

## Evidence

- Source inventory: `/Users/charles/.hermes/docs/private/dirty-inventory-20260604-after-cache-clean/inventory.csv`
- Deep inventory index: `/Users/charles/.hermes/docs/private/dirty-inventory-20260604-deep/index.json`
- Scripts diff cluster: `/Users/charles/.hermes/docs/private/scripts-diff-cluster-20260604/summary.json`

## Ranking

1. `media/generated` — count 338 — gate `mechanical-review`
   - Verify file types + regeneration source, then consider narrow ignore/archive. No commit/delete before review.
2. `notes/generated-reports` — count 107 — gate `mechanical-review`
   - Generated reports may be documentation artifacts; decide keep latest vs archive, do not bulk delete.
3. `runtime/logs` — count 35 — gate `mechanical-review`
   - Runtime logs likely ignorable after confirming no audit logs needed.
4. `runtime/db-lock` — count 38 — gate `manual-protected`
   - Locks/state adjacent; confirm no live process and no DB corruption before any ignore/delete.
5. `runtime/state` — count 48 — gate `manual-protected`
   - Runtime state can encode active queues/sessions; no reset/delete without explicit gate.
6. `scripts/local-control-plane` — count 239 — gate `scripted-with-review`
   - Highest-value semantic audit after generated/runtime review; cluster by function and commit coherent capabilities only.
7. `other` — count 227 — gate `manual-triage`
   - Mixed bucket; split before action.
8. `profile/config-cache` — count 9 — gate `manual-only`
   - Config/quorum protected; redact and diff each if needed.
9. `skills/active` — count 620 — gate `manual-only`
   - Active skill semantic changes; review skill-by-skill, patch skill only when intent clear.
10. `brain/workpad` — count 312 — gate `manual-only`
   - Local brain/workpad SSOT; source-of-truth review required.
11. `profile/memory` — count 4 — gate `manual-only`
   - Memories are durable user/system state; no bulk edits.
12. `profiles/cross-profile` — count 993 — gate `manual-only`
   - Cross-profile homes; no modifications without explicit user direction.
13. `submodule/hermes-agent` — count 2 — gate `separate-repo`
   - Handle inside its own git worktree only.

## Stop conditions

- Any proposed action touches config, DB, memory, cron jobs, cross-profile homes, active skills, brain/workpad SSOT, or inner `hermes-agent` without explicit manual approval.
- Any staged diff includes paths outside the current scoped allowlist.
- Live inventory drifts in a way not explained by decision artifacts.
- A bucket cannot be classified as generated/runtime/semantic with path-only evidence.

## Commit authorization for this round

Allowed: docs/private decision evidence, deep inventory, scripts diff cluster, ranked plan, and prompt/state files from this multi-model decision. Not allowed: operational scripts, skills, profiles, configs, memories, DBs, runtime state, generated media, or .gitignore changes.
