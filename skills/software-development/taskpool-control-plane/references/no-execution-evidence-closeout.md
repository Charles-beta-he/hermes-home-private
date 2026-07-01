# No-execution evidence tasks should not require UI/API closeout proof

## Applicability

Use when a Hermes/local-brain task is in `review` and `auto-close-review` or `done` blocks with `execution_flow_closeout_blocked:browser_or_ui_surface_proof` or `api_or_backend_readback_proof`, but the task is an evidence/intake/source-identification task rather than an implementation task.

Common frontmatter signals:

- `lane: evolution` or another non-`work` lane
- `workflow_stage: evidence`, `intake`, `source-identification`, or `source_identification`
- `completion_boundary: taskpool_candidate`
- `harness_surfaces` includes `no-execution` / `no execution`
- acceptance/red-lines explicitly say no install, no execution, no scanning, no SaaS upload, no code copying, or public-preview/read-only only

Anti-conditions:

- Do not apply to `lane: work` implementation tasks.
- Do not apply when the task actually delivers UI/API/frontend/backend behavior.
- Do not satisfy real implementation closeout with source-analysis notes; real work tasks still need test/build/browser/API/readback evidence as applicable.

## Debugging path

1. Read the task frontmatter and body before accepting the closeout error.
2. Classify `browser`, `preview`, `UI`, `API`, `verify`, and similar words as either:
   - source/evidence surfaces being analyzed, or
   - implementation surfaces being delivered.
3. If the task is explicitly no-execution evidence intake, treat UI/API closeout proof as a false positive.
4. Keep the deterministic gate evidence: source-identification note, evidence bundle, recommendation matrix, ratification/selfcheck/proof evidence as required by the task's `completion_gate`.
5. Add/keep a regression: a non-work evidence task that mentions browser/public-preview/no-execution should close with evidence/proof artifacts, while a true work task that implements browser UI/API remains blocked without UI/API proof.

## Verification checklist

- Targeted regression for no-execution evidence intake passes.
- Existing regression for work-lane browser/API implementation still blocks without proof.
- `py_compile` passes for orchestrator/test files.
- Live `auto-close-review --task <task>` closes only after evidence gates pass.
- `selfcheck` and `proof-check` remain PASS.

## Related ratification packet pitfall

Review-gap repair children may carry parent-bound deterministic packets such as `multimodel_ratification_v1` with `certification_result=PASS`, `loop_done=true`, `parent_task_id`, and `repair_child_task_id`. Consume these only through target-bound read-compatible repair logic; do not relax the strict ratification gate for new discussion artifacts.
