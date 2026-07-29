# AutoDev Studio → Hermes ReferenceReview SSOT

```yaml
schema: hermes_reference_review_v1
id: autodev-studio-20260729
source_repo: https://github.com/krishagarwal314/autodev-studio
source_commit: 6cef552bc69fba7876fe9813ab96fc001ab66970
source_tree: f8379d001cc20ef2eacaa4c3b82ca684b0a384cb
local_checkout: /Users/charles/.hermes/runs/autodev-studio-reference-review-20260729/source
status: absorption-pack-verified-no-runtime-change
canonical_ssot: /Users/charles/.hermes/docs/private/autodev-studio-absorption-20260729/PLAN.md
authority: external-read + local-document-write only
```

## Objective
Absorb source-proven contracts for persistent project knowledge, symbol-grounded context, test-baseline differential, honest usage receipts, evidence write-back and typed fail-closed verdicts.

## Non-goals
- No AutoDev install/import into Hermes; no parallel scheduler/taskpool/provider registry/knowledge truth.
- No Hermes core/runtime/routing/gateway/task lifecycle/cron/external delivery/publish/deploy/push/credential/destructive mutation.
- No promotion of upstream benchmark economics as reproduced Hermes results.

## Loop contract
```yaml
objective: verified source-to-capability absorption pack
baseline_ref: 6cef552bc69fba7876fe9813ab96fc001ab66970/f8379d001cc20ef2eacaa4c3b82ca684b0a384cb
acceptance: [source claim hashes pass, graph contract passes, overlap recorded, tamper and authority negative controls pass]
budgets: {max_iterations: 4, max_repeated_failure: 2, max_side_effect: local_document_write}
authority: {exact_target: /Users/charles/.hermes/docs/private/autodev-studio-absorption-20260729, prohibited: [core mutation, runtime enablement, scheduler, lifecycle, external dispatch, publish, deploy, push, credential entry]}
stop_conditions: [verified pack, source drift, tooling blocker, exact authority boundary]
```

## Existing Hermes overlap
Fresh inspection found existing `CompletionGate`, lane-specific `completion_gate_failures`, `PASS_ADVISORY_ONLY` separation and certification evidence gates in `scripts/task_adapter.py` and `scripts/brain_task_orchestrator.py`. Therefore this pass creates no second runtime gate. The remaining falsifiable question is whether every real consumer rejects `ERROR / INCONCLUSIVE / MISSING / STALE` and binds PASS to current artifact identity.

## Decisions
Immediate landing: pinned claim map, CapabilityGraph, proposal-only atoms and read-only pack verifier. Runtime knowledge consumer, completion-gate changes and provider routing remain blocked until a current Hermes failing repro, offline replay and independent review exist. External PR/push/deploy additionally requires exact target, authority, rollback and readback.

## Artifacts
- `evidence/source-evidence.json`
- `evidence/timestamped-source-packet-20260729.md`
- `graph/raven-everos-capability-graph.json` (legacy generic-checker filename)
- `proposals/experience-ratchet-created.json` (proposal-only; no durable promotion)
- `scripts/verify_pack.py`; `tests/test_verify_pack.py`; `reports/final.md`
