# Multi-model decision request: Hermes root dirty-state governance

We need decide the next governance action for `/Users/charles/.hermes` after a scoped cleanup commit.

Evidence already gathered:

- Repo: `/Users/charles/.hermes`, branch `master`.
- Latest scoped commit: `bfefab0 Add Hermes dirty-state governance inventory`.
- A reusable classifier exists at `/Users/charles/.hermes/scripts/hermes_dirty_inventory.py`.
- Governance report exists at `/Users/charles/.hermes/docs/private/hermes-dirty-state-governance-20260604.md`.
- Current inventory summary after safe cleanup:
  - total dirty/untracked: 3004
  - untracked: 2507
  - modified: 288
  - deleted: 209
  - high risk: 2213
  - critical: 4
  - medium: 414
  - low: 373
  - major buckets: profiles/cross-profile 993, skills/active 620, media/generated 338, brain/workpad 312, scripts/local-control-plane 239, other 227, notes/generated-reports 107, runtime/state 48, runtime/db-lock 38, runtime/logs 35.
- Safe actions already done:
  - ignore `cron/output/`, `__pycache__/`, `*.py[cod]`, `*.log.*`, Python cache dirs.
  - remove Python bytecode/cache artifacts.
  - commit deletion of one tracked pyc file.
- No config, memory, database, active skill, brain/workpad, or semantic script changes were reset/deleted/committed.

User wants “多模型思考决策” and then “继续”: decide how to proceed, not merely summarize.

Hard constraints:

1. Do not blanket reset, clean, ignore, or commit remaining dirty state.
2. Treat these as manual/high-risk gates unless a model gives strong, evidence-backed narrow exception:
   - `config.yaml`, `config/quorum.yaml`, `cron/jobs.json`
   - `state.db`, `route_outcomes.db`, `gateway_state.json`, locks
   - `memories/**`
   - `profiles/**` cross-profile homes
   - `notes/brain/**` workpad/local-brain SSOT
   - active `skills/**` semantic changes
   - inner repo `/Users/charles/.hermes/hermes-agent`
3. User preference: production-long-term governance, no lost functionality, no precision downgrade, no ghost memory writes, scoped commits only.
4. Hermes profile rule: do not modify another profile’s skills/plugins/cron/memories unless user explicitly directs it.
5. Prefer evidence-first, cluster-by-cluster decisions.

Question for models:

What should be the next concrete action sequence for this dirty-state governance? Choose among or refine these candidates:

A. Stop and ask user to choose from the four high-risk batches.
B. Proceed read-only with deeper cluster inventories for `scripts/**`, `skills/**`, `profiles/**`, and protected config/db/memory, then present a ranked plan.
C. Begin implementing a narrow policy change, e.g. ignore selected generated dirs (`logs/*.jsonl`, `image_cache`, `browser_replay_evidence`, `profiles/**`) without further review.
D. Start semantic audit of `scripts/**` first and commit coherent clusters.
E. Start `skills/**` reconciliation first.

Return:
- vote: approve/amend/reject for a proposed next step.
- recommended next step, exact scope, and stop conditions.
- risks and mitigations.
- any commands that should be run before side effects.
