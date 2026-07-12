# Closeout Surface Obligation Classifier

Use when taskpool `review -> done` is blocked by `execution_flow_closeout_blocked:browser_or_ui_surface_proof` or API/UI proof on a task that may only be read-only evidence intake.

## Problem pattern

Regex-only closeout gates are too rigid. Words such as `browser`, `public preview`, `API`, `verify`, or `验证` may describe the *source/input surface* being analyzed, not a UI/API implementation output that needs browser/API smoke proof.

False-positive example: a WeChat public-preview/source-identification task with:

- `workflow_stage: evidence`
- `completion_boundary: taskpool_candidate`
- `harness_surfaces: public-preview / external-search / no-execution`
- red lines such as no install, no execution, no scanning

This should not require UI/browser implementation proof; it should close from deposited evidence + ratification/selfcheck proof.

## Recommended decision model

Prefer a deterministic classifier with reasons over a single hard exemption:

1. **Advisory evidence gate**: advisory + `advisory-evidence-review-done` closes from deposited report/evidence.
2. **Manual partial closeout**: `manual_review_approval_action=approve_close_as_partial` should not be blocked by implementation proof requirements.
3. **Work lane fail-closed**: `lane=work` still requires structured evidence and UI/API proof when UI/API terms are present.
4. **No-execution source intake**: non-work tasks with no-execution/no-install/no-scanning plus source-intake signals (`workflow_stage=evidence`, `completion_boundary=taskpool_candidate`, `harness_surfaces=public-preview|external-search|source-identification`) should not require implementation UI/API proof.
5. **Non-work output obligation**: if non-work task still has explicit output/implementation surfaces or verbs, require implementation proof.
6. **Explicit harness surfaces override incidental prose**: when `harness_surfaces` is a non-empty governed list, derive UI/API requirements from that list (`browser|ui`, `api|backend`) rather than scanning historical body prose. A task with `harness_surfaces: [local-cli]` must not require screenshots merely because its research/non-goals mention “browser” or “UI”. If harness surfaces are absent, conservative text inference remains appropriate.
7. **Semantic intent is a separate gate**: a legacy active task may also fail with `semantic_intent_missing_needs_review`. Add a valid versioned envelope only when its requested outcome, capability, lane, task class, side-effect class, sources, and evidence gates are true. Validate the envelope through the canonical evaluator before writing it. Do not mark `semantic_contract_status: validated` unless the associated hash-bound knowledge-recall receipt is actually present and source-verifiable.
8. **Fallback**: non-implementation tasks without output obligation do not need execution-flow proof.

Always return a reason list (for audit) such as `lane_work_fail_closed`, `source_intake_surface`, `no_execution_boundary`, or `non_work_but_output_obligation`.

## Verification

Regression set should include:

- Source-intake/no-execution task mentioning browser/public-preview -> classifier says no execution-flow proof required and transition can close with evidence/ratification proof.
- Explicit `harness_surfaces: [local-cli]` plus historical body/non-goal mentions of browser/UI -> implementation proof remains required, but UI proof is false and API proof is false.
- Explicit `harness_surfaces: [backend]` -> API/readback proof is required but UI proof is false.
- Work-lane UI/API implementation without explicit bounded surfaces -> still blocks without browser/API/readback proof.
- A legacy review task missing semantic intent -> RED closeout first; add and evaluate a truthful envelope, then rerun the normal gate instead of forcing the status.
- Invalidly setting `semantic_contract_status: validated` without a canonical knowledge-recall receipt -> fail closed; remove the unsupported certification marker or generate/verify the real receipt.
- Manual partial closeout -> remains closable with selfcheck/proof evidence.
- Run focused classifier/transition tests first, then the full orchestrator suite, validator/reindex/exhaustive audit, task list, selfcheck, and proof-check after live closeout.
- Require the normal lifecycle transition to mint/read back its proof hash; a verifier PASS alone is not a status mutation receipt.

## Multi-model review lesson

A degraded multi-model review can still be useful as advisory design input. In the Security Ark closeout repair, Claude/DeepSeek agreed on replacing the rigid exemption with a classifier, while GPT failed/unparseable and truth coverage was not certified. Treat such output as design guidance, then land deterministic tests and objective readbacks before claiming completion.
