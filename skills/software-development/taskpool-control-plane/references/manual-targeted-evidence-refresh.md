# Manual targeted-evidence refresh for blocked parents

Use when:
- Finished convergence children already exist, but the parent still shows `multimodel_status: not_certified` and `multimodel_last_decision: CONTINUE_LOOP`.
- You need a fresh parent-level multimodel pass without changing the frozen parent objective.
- `auto-split-non-convergence` from older artifacts is no longer enough to explain the remaining blockage.

## Proven sequence

1. Create a manual state packet under `~/.hermes/state/taskpool-multimodel/`.
   - Freeze the original parent objective.
   - Cite canonical parent task note, frozen-objective artifact, and the finished child briefs / final-design artifact.
   - Phrase the ask as a targeted evidence fix, not a new design brief.
   - **Bind truth claims explicitly.** Do not rely on prompt prose or `--context-json` alone; `ratification-gate` can still fail with `truth_gate_failed:no_claims` / `target_task_binding_missing` even when the prose contains evidence. Include `--claim` entries for the concrete facts that must be certified, for example:
     - `target_task:<parent-id> is the certification target and the frozen objective is unchanged`
     - `probe_scope: refreshed probe is read-only/no-credentials/no-write/no-spend`
     - `artifact_hash: <artifact> has sha256 <hash>`
     - `acceptance_mapping: each original acceptance criterion is satisfied or explicitly residual`
   - Pair the claims with `--evidence-json` objects or artifact paths that ground each claim, and include verification commands (`py_compile`, probe rerun, readback/hash) in `--verify`.

2. Run a real discussion round:
   - `python3 ~/.hermes/scripts/consult_models.py run <state.json> --tier T3 --quorum 4 --discussion --max-rounds 3 --keep`

3. Gate the new artifact:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py ratification-gate --task '<parent-id>' --discussion-result '<tick.../discussion_result.json>' --json`

4. Even if the gate still FAILs, persist the new round into the parent through the orchestrator write path.
   - The important effect is updating:
     - `multimodel_last_discussion_artifact`
     - `multimodel_last_failures`
     - `multimodel_last_gate_status`
     - `multimodel_last_decision`
   - This keeps later `auto-split-non-convergence` and blocked-resolution logic grounded in the newest parent evidence, not stale historical FAIL metadata.

5. Re-run `auto-split-non-convergence` and then `auto-subtask-sync --write`.

6. Verify with:
   - `next --json`
   - `list --json`

## Failure signatures captured in sessions

### Refresh exposes a new actionable axis

The refreshed discussion can still be `not_certified`, but it may expose a new actionable axis:
- new `issue_ledger` entries
- new `recommended_axes`
- explicit disagreement in `vote_reject` / `agreement_low`
- `planner_patch_summary.certification_intent = unresolved_noop_vs_change`

That combination justified creating fresh child work even though older children had already been completed.

### Refresh fails because claims were only in prose

A targeted refresh can produce a real `discussion_result.json` but still fail the taskpool gate when the `consult_models.py state` packet contains no explicit claims/evidence bundle:
- `fanout_certification.status = degraded_not_certified` because planner quorum fell below min quorum;
- `truth_assessment.truth_status = no_claims`;
- `ratification-gate` failures include `truth_gate_failed:no_claims`, `target_task_binding_missing`, `accuracy_criterion_missing`, and `long_term_goal_alignment_missing`.

This is not proof that the parent objective is wrong. Treat it as a malformed certification packet. Next action: regenerate the state with explicit `--claim` / `--evidence-json` bindings and rerun the discussion before splitting more children, unless the fresh taxonomy also names a clearly missing axis. If you persist the failed round, mark it as `CONTINUE_LOOP` evidence only, then run `auto-split-non-convergence` / `auto-subtask-sync --write` so the pool can continue safely.

## Pitfall: the generated child set may have incomplete axis coverage

`build_non_convergence_subtask_specs()` limits output to three axes. In practice this can omit `framing` when the refreshed parent taxonomy recommends four axes.

Checklist after refresh:
1. Inspect the refreshed FAIL taxonomy.
2. Compare its recommended axes with the actual `auto_subtask_children` set.
3. If `framing` is still recommended but absent from children, create an explicit framing child and resync the parent.

## Expected good outcome

A successful refresh does not need to unblock the parent immediately.
A valid intermediate win is:
- parent stays `blocked`
- new child axis becomes `pending` and dispatchable
- `next --json` returns that child instead of `null`

That means the pool regained safe forward progress.