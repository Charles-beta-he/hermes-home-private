# Local-brain auto-constraint gate landing pattern

Use when the user asks to fully land a local-brain / workflow-control-plane constraint layer, especially after wording such as “调用两种功能”, “全量自动约束层”, “接入并开启”, or “不要只做文档”.

## Class-level lesson

Do not split review/routing into a separate final artifact when the user’s target is the main constraint layer. Treat supporting functions, such as local-brain retrieval and multi-model RouteReview, as sub-gates folded back into the canonical BrainConstraintGate plan and executable entrypoints.

## Safe landing ladder

1. Canonical plan contract
   - Mark the main plan as the stable/canonical target.
   - State which layers are actually live versus future runtime goals.
   - Keep model review advisory unless quorum and non-model evidence prove certification.

2. Local dry-run gate
   - Add a standalone CLI that emits a structured BrainConstraintRecord and embedded RouteReviewRecord.
   - Search all relevant brain vaults, not just the default vault.
   - Expand recall queries from task summaries so verbs like “完善/强化/修改” do not prevent canonical-note matches.
   - Include side-effect booleans that remain false by default.

3. Unified brain CLI entrypoint
   - Add a `brainctl preflight` wrapper so the gate is discoverable from the local-brain control plane.
   - Return non-zero only for block/quarantine states; warn is not success certification but should not prevent local read-only progress.

4. Intake/workflow integration
   - Embed the preflight result in task-intake records under a stable key, e.g. `local_brain_constraint`.
   - If the gate blocks, mutate only the local preflight/intake state to `blocked_by_local_brain_constraint`; do not write taskpool lifecycle done/failed unless a separate lifecycle gate is explicitly opened.
   - Provide an env kill-switch, e.g. `HERMES_LOCAL_BRAIN_PREFLIGHT_ENABLED=0`.

5. Local commit hook activation
   - Install a reversible local pre-commit hook only after focused tests pass.
   - Preserve any previous hook as a backup.
   - The hook may run py_compile, focused tests, and `brainctl preflight`; it must not dispatch externally, write lifecycle state, publish/deploy, or perform destructive actions.
   - Add exact target, rollback, and post-action readback evidence so the hook’s own preflight is non-blocking.

6. Runtime/lifecycle boundary
   - Stop before runtime hard gates, taskpool lifecycle write-through, cron workers, external dispatch, publish/deploy/push, destructive operations, or credential/payment entry unless an exact target, rollback path, receipt, and readback have been separately authorized.

## Pitfalls

- Separate-artifact drift: creating a polished RouteReview document but not folding it into the main auto-constraint layer misses the user’s target.
- Summary-AND recall miss: conservative FTS searches over full change summaries can miss canonical notes because action verbs are absent. Generate smaller noun/surface queries.
- Canonical-policy self-demotion: a current policy note may mention stale markers such as “without tests” or “no proof” as filter criteria; do not demote the policy itself if its frontmatter marks it current/canonical.
- Evidence-repair loop: if the gate blocks because local writes require `exact_target`, `rollback`, or `post_action_readback`, add those evidence refs rather than weakening the gate.
- Hook-as-runtime trap: a local pre-commit hook is an enabled local boundary, not proof that Hermes runtime/taskpool/cron hard gates are live.

## Verification checklist

- Focused tests cover: multi-vault search, current-vs-stale selection, block on missing evidence, CLI parseable JSON, and no external/lifecycle side effects.
- Main local-brain tests still pass.
- Architecture/theory ratchet still passes when pointed at the notes brain.
- `brainctl search` can find the canonical plan and marks it accepted, not filtered.
- Installed hook status reads back enabled.
- A real commit or hook run proves the hook invokes the gate and returns non-blocking only with required evidence.
- Final report distinguishes: live local gates versus unopened runtime/lifecycle/external gates.
