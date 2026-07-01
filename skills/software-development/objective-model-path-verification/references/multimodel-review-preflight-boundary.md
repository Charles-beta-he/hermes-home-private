# Multi-model review preflight boundary

Scope: Hermes/control-plane or workflow-kernel boundary advancement where a local advisory/route-preflight surface is already enabled and the user authorizes continuing to open boundaries, while execution/tool/lifecycle/external gates are still closed.

Applicability: use when the next safe advancement is not an executor, but a review/certification precondition before any future executor or write-through gate. Typical wording: "继续推进打开" plus "每一步补充多模型智能 review / 扩展安全边界".

Anti-conditions:
- Do not use this as authority to invoke tools from Agent OS, spawn workers, schedule cron, mutate taskpool/mission lifecycle, send external messages, push/deploy/publish, or perform destructive actions.
- Do not treat model votes alone as execution authority. They can open a review-only preflight boundary only when paired with local readback/test evidence.
- Do not call certification complete if the truth gate failed due to evidence-link mismatch; repair evidence IDs and rerun.

## Procedure

1. Read back the current boundary first (`status`/doctor/projection) and record which neighboring gates are still false.
2. Add a default-off config flag for the review preflight (for example `agent.<feature>_multimodel_review`).
3. Add prompt/runtime guidance that says future expansion beyond route/advisory preflight requires independent multi-model/adversarial review or a recorded degraded-review packet with objective evidence.
4. Keep the guidance review-only: it must explicitly say execution gates remain closed until a later exact AuthorityGrant and fresh readback open that specific gate.
5. Add live status/readback fields for the new review flag and for every still-closed neighboring gate available in that surface.
6. Add tests for:
   - default-off omits the review guidance;
   - no-tools omits the guidance;
   - enabled config injects the guidance;
   - status/readback shows review enabled while execution/external gates remain false;
   - absent config defaults to review=false and execution gates false.
7. Run deterministic tests and an independent code review for the diff before committing.
8. Run multi-model certification as review-package/no-action certification. Use claim IDs and evidence `supports` IDs that match the orchestrator-normalized IDs (often `C-001` rather than an ad-hoc label like `C1`). If the first run returns `truth_not_certified` only because of ID mismatch, correct the evidence binding and rerun before claiming certification.
9. Update the project SSOT/ledger/gates index with the consumed boundary, readback, test evidence, review result, and still-closed gates.
10. Commit scoped code/tests only; keep project profile/ledger updates in their own SSOT landing if they are outside the repo.

## Verification shape

- Live config/readback: review preflight true, route/advisory state unchanged, tool invocation false, external dispatch false.
- Fresh prompt construction includes the review preflight text and an explicit "keep execution gates closed" statement.
- Focused tests pass.
- Independent reviewer returns `passed=true` with no security or logic blockers.
- Multi-model certification manifest shows `status=certified`, `can_claim_complete_certification=true`, `truth_grounded=true`, and `planner_patch_intent=no_action_certification` for the review-only boundary.

## Pitfalls

- A broad user phrase like "全部允许" or "继续打开" should be consumed one boundary at a time; review preflight is often the next smallest safe boundary before executor activation.
- If a multi-model run certifies fanout quorum but fails truth grounding, do not call it certified. Repair evidence links or report degraded/not-certified.
- Adding the review gate after a previous code-review PASS changes the reviewed diff; rerun deterministic tests and final independent review.
