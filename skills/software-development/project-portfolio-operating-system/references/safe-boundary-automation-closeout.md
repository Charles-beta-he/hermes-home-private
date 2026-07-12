# Safe Boundary Automation Closeout

Applicability: use for portfolio-governance or multi-project closeouts where the user authorizes continued progress, but remaining work mixes local reversible automation with authority-sensitive boundaries.

Scope marker: this is a reusable procedure. Concrete project IDs, artifact paths, mission IDs, branches, URLs, and counts belong in that project profile, ledger, or closeout manifest, not in this reference.

## Classify before acting

Partition each remaining boundary into:

- `safe_local`: local, reversible, no external dispatch, no credential/payment/destructive action, no production deploy/push, and verifiable by readback.
- `exact_authority_needed`: push/deploy/external send, lifecycle/worker/scheduler enablement beyond local receipt, payment/credential entry, destructive operation, or production promotion.
- `evidence_needed`: missing runtime artifact, missing screenshot/readback, stale doctor state, or unsupported maturity claim.
- `acceptance_needed`: subjective A+/uIMax-final visual acceptance or product-direction choice.

Only run `safe_local` items under broad continuation authorization. Do not convert broad trust into external/production authority.

## Safe local automation pattern

1. Capture a compact objective model: goal, blocked actions, evidence requirements, and rollback/readback plan.
2. For each safe slice, create or update local artifacts only.
3. Verify with real readback, not status labels:
   - CLI JSON output or script test;
   - browser/screenshot readback for UI/demo surfaces;
   - mission doctor for taskpool/mission state;
   - semantic audit/portfolio doctor/strict verify for portfolio metadata.
4. Update profile/registry/ledger only to the maturity level proved by the evidence.
5. Write a closeout manifest with hashes/paths, explicitly listing preserved blocked boundaries.
6. If an independent verifier is available, ask it to review the manifest for overclaim; treat it as advisory unless backed by artifacts.

## Proven slice patterns

### Local runtime demo

Allowed under safe local scope:
- static Web/CLI demo;
- negative authority contract (`external_send=false`, `voice=false`, `deploy=false`, `secret=false`, `destructive=false`);
- CLI JSON readback and browser readback.

Do not claim production runtime, default voice, external send, or real assistant behavior until a concrete surface and exact authority are selected.

### Mission/taskpool stale-signal recovery

Allowed under safe local scope:
- bounded local-ledger recovery batches against the exact mission/task identifier;
- stop when doctor reports pending/stale signals `0` or when recovery requires task execution/external side effects;
- doctor readback after the loop.

Pitfall: a resume command alone can be false restoration if tick budget remains exhausted. Always read back tick budget, open decisions, pending signals, stale signals, script path, and scheduler/cron status.

### Operator UI / uIMax local report

Allowed under safe local scope:
- use existing harness screenshots and summaries;
- generate a local uIMax report;
- grade honestly (for example `B+ local-operator-ready`) and explicitly say `not A+` when keyboard-flow, contrast-token, or taste acceptance evidence is missing.

Do not call this production-ready UI or A+ unless the uIMax evidence matrix is complete.

## Closeout manifest fields

Minimum useful fields:

```json
{
  "scope": "local reversible safe boundary automation",
  "completed_slices": {
    "local_runtime_demo": {"status": "pass", "external_side_effects": []},
    "stale_signal_recovery": {"before_pending": 0, "after_pending": 0},
    "operator_ui_uimax_report": {"grade": "B+", "not_a_plus": true}
  },
  "blocked_boundaries_preserved": ["push", "deploy", "external_dispatch", "credential_entry", "payment", "destructive_action", "production_runtime_promotion", "A+ UI acceptance"],
  "artifacts": [{"path": "...", "sha256": "..."}]
}
```

## Anti-conditions

- Do not store session progress as a skill; this reference stores the reusable closeout procedure only.
- Do not hardcode one project’s paths as global truth; put concrete paths in the project profile/ledger/manifest.
- Do not let a green portfolio doctor promote production claims; portfolio PASS is only as broad as its evidence and blocked-boundary list.
