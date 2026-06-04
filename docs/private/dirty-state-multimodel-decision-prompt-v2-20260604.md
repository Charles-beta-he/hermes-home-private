# Multi-model decision request v2: Hermes dirty-state governance after evidence fulfillment

We need make a practical governance decision for `/Users/charles/.hermes` dirty/untracked state.

This is a decision round, not an implementation authorization round. Concrete writes must still be separately scoped and verified.

Verified evidence:

- Evidence artifact: `/Users/charles/.hermes/docs/private/dirty-state-multimodel-evidence-20260604.json`
- Inventory summary artifact: `/Users/charles/.hermes/docs/private/dirty-inventory-20260604-after-cache-clean/summary.json`
- Inventory CSV: `/Users/charles/.hermes/docs/private/dirty-inventory-20260604-after-cache-clean/inventory.csv`
- Latest committed governance baseline: `bfefab0` originally, amended final dirty-governance commit is `bfefab0`/later local history; verify with git log if needed.
- The committed inventory snapshot after cleanup says: total 3004; high 2213; critical 4; untracked 2507; modified 288; deleted 209.
- A live `git status --porcelain=v1` after creating this decision evidence artifact shows 3007 entries (`{' M': 288, ' D': 209, '??': 2510}`), explained by newly created decision prompt/evidence artifacts. The delta is local decision artifacts, not a substantive governance change.
- Major buckets from committed inventory:
  - profiles/cross-profile: 993
  - skills/active: 620
  - media/generated: 338
  - brain/workpad: 312
  - scripts/local-control-plane: 239
  - other: 227
  - notes/generated-reports: 107
  - runtime/state: 48
  - runtime/db-lock: 38
  - runtime/logs: 35
  - profile/config-cache: 9
  - profile/memory: 4

Previous T1 multi-model run:

- Models consulted: claude-opus-4-7, gpt-5.5, mimo-v2.5-pro, deepseek-v4-pro.
- It was not certified because the factual count claim was not linked to evidence in the state packet, and because models split between noop/advisory and concrete read-only artifacts.
- Despite non-certification, the substantive trend was: do not proceed with destructive cleanup; prefer read-only deeper cluster inventories and ranked plan; scripts first is plausible after evidence; skills/profiles/brain/config/db/memory remain manual gates.

Hard constraints:

1. No blanket reset, clean, ignore, or commit of remaining dirty state.
2. No cross-profile modifications without explicit user direction.
3. No config/db/memory/cron/jobs/protected runtime writes without explicit manual approval.
4. No active skill semantic bulk change without skill-level review.
5. No brain/workpad SSOT reset/commit without source-of-truth review.
6. Scoped commits only, with verification.
7. User wants a decision and continued progress until manual intervention is truly required.

Decision options:

A. Stop now and ask the user to pick a batch.
B. Proceed read-only by generating deeper cluster inventories and a ranked execution plan, then commit only the decision artifacts.
C. Add broad .gitignore rules for generated-looking dirs such as media/generated, browser_replay_evidence, logs/*.jsonl, profiles/**.
D. Start semantic audit of scripts/** first, but with read-only diff clustering before any script commit.
E. Start skills/** reconciliation first.

Question:

What is the best next action under the constraints? Return a decisive recommendation with:
- vote: approve/amend/reject for option B+D hybrid if appropriate.
- exact next scope.
- stop conditions.
- what is allowed to be committed now, if anything.
- what must remain behind manual gates.
