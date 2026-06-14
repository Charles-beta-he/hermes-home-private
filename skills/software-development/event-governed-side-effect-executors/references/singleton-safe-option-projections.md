# Singleton safe option projections

Scope: localhost/operator control planes and task/execution-flow gates that are already classified as requiring a safe non-mutating next step.
Applicability: use when the gate has been reduced to a finite set of safe decisions and exactly one may be preselected without granting execution authority.
Anti-condition: do not use this pattern to auto-approve, dispatch workers, mark done, send/publish/delete, mutate production state, or perform external adapter writeback.

Use this pattern when a task/control-plane gate has been reduced to exactly one safe, non-mutating next step. The goal is to remove pointless human clicks without turning a safe-path selection into execution authority.

## Classification

The task/control-flow layer should be the source of truth for option generation:

- Evidence or proof gaps produce one safe option: `needs_more_evidence` with `resumeMode=repair`.
- Hard authority boundaries produce one safe option: `hold` with `resumeMode=hold`.
- Hard boundaries include permission, external side effects, destructive actions, credentials, value judgement, and safety/legal gates.
- Hard boundaries dominate evidence gaps. A blocked task that also has pending external side effects must project `hold`, not `needs_more_evidence`.
- No-boundary tasks should not invent a human-gate option.

## Projection contract

A read-only evaluator may emit:

```json
{
  "safe_decision_options": [
    {"decision": "hold", "label": "暂停", "resumeMode": "hold"}
  ],
  "auto_decision": {
    "decision": "hold",
    "label": "暂停",
    "resumeMode": "hold",
    "reason": "single_safe_option"
  }
}
```

Downstream dashboards must treat this as draft/preselect state only. It is not a recorded decision, not an approval, and not executor authority.

## Consumer hardening

Consumers such as control consoles should not trust upstream option labels or arbitrary decisions. Apply an allowlist before display or submission:

- Allow only `needs_more_evidence + repair` and `hold + hold` for safe-gate choices.
- Canonicalize labels locally; do not trust upstream labels that imply acceptance or approval.
- Drop accept, approve-with-edit, closeout, dispatch, worker, send, publish, delete, or any other unsafe decision from safe-gate choices.
- Only show an auto-selected UI state when upstream `auto_decision` exactly matches the single sanitized safe option. Do not synthesize `auto_decision` in the projection layer just because one option remains.
- Keep auto-selected visually distinct from submitted/ledgered state.
- On submit, build the payload from the sanitized decision id and resume mode, not from a free-form label-to-contract map.
- Safe gates must remain fail-closed for dispatch, worker execution, done closeout, and external writeback even when local capability sessions are armed.

## Regression tests

Add tests for:

- evidence-only blocked task -> `needs_more_evidence` auto decision;
- blocked task with pending external side effects -> `hold` auto decision;
- unsafe upstream option is dropped;
- mismatched or absent upstream `auto_decision` does not become auto-selected;
- multiple safe options do not auto-select;
- UI auto-selected state is not submitted state;
- submit path uses canonical safe decision/resumeMode instead of generic label contracts;
- dispatch/worker/external writeback remain blocked for safe gates.
