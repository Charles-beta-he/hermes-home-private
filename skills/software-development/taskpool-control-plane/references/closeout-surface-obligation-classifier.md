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
6. **Fallback**: non-implementation tasks without output obligation do not need execution-flow proof.

Always return a reason list (for audit) such as `lane_work_fail_closed`, `source_intake_surface`, `no_execution_boundary`, or `non_work_but_output_obligation`.

## Verification

Regression set should include:

- Source-intake/no-execution task mentioning browser/public-preview -> classifier says no execution-flow proof required and transition can close with evidence/ratification proof.
- Work-lane UI/API implementation -> still blocks without browser/API/readback proof.
- Manual partial closeout -> remains closable with selfcheck/proof evidence.
- Full taskpool selfcheck/proof-check after live closeout.

## Multi-model review lesson

A degraded multi-model review can still be useful as advisory design input. In the Security Ark closeout repair, Claude/DeepSeek agreed on replacing the rigid exemption with a classifier, while GPT failed/unparseable and truth coverage was not certified. Treat such output as design guidance, then land deterministic tests and objective readbacks before claiming completion.
