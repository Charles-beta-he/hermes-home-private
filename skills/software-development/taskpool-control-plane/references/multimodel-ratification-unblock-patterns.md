# Multimodel ratification unblock patterns

Use this reference when a blocked task has a multimodel certification artifact but `blocked-resolve-step`, `ratification-gate`, `proof-check`, or `lifecycle` still disagree.

## Safe unblock sequence

1. Re-run or regenerate the discussion artifact only through the certification tooling.
2. Ensure the artifact is explicitly bound to the target task:
   - `target_task_id`
   - `target_task_path`
   - optionally mirrored under `context.target_task_id` / `context.target_task_path`
3. Run `ratification-gate --task <id> --discussion-result <artifact> --json`.
4. If PASS/LOOP_DONE, write the task frontmatter authority fields:
   - `multimodel_status: certified`
   - `multimodel_last_gate_status: PASS`
   - `multimodel_last_decision: LOOP_DONE`
   - `multimodel_ratification_artifact: <absolute artifact path>`
   - `ratification_artifact: artifact:<absolute artifact path>` when the task is a mission envelope.
5. Run `blocked-resolve-step`; then `auto-close-review` only if normal review closeout gates pass.
6. Verify with `selfcheck`, `proof-check`, and `lifecycle`.

## Pitfall: self-relaxing governance patches

If a minority model proposes changing ratification thresholds, gate quorum, certification policy, or control-plane governance so the current failed certification becomes easier to pass, do not treat that as a current implementation patch and do not adopt it to unblock the same task.

Classify it as deferred/advisory governance work when all are true:
- minority concrete patch;
- other models are noop/no-change;
- target touches ratification/certification/gate/control-plane code;
- rationale is to unblock this failed certification via lower threshold/quorum/single-model approval.

This avoids the loop: certification fails -> patch certification rules -> certification passes.

## Pitfall: legacy evidence strings

Historical task evidence may contain shorthand such as:
- `child-task:...`
- `child-axis:...`

Lifecycle and proof gates expect structured evidence prefixes (`proof:`, `artifact:`, `file:`, `command:`, etc.). For existing legacy audit notes, normalize by prefixing `proof:` or filter them out of resolver-generated transition evidence while adding a structured ratification artifact. Do not weaken lifecycle gate validation.

## Pitfall: optional model votes treated as gate failures

In `brain_task_orchestrator.py`, the `ratification_gate_result()` function checks all votes for `non_approve_vote` and `best_within_constraints_missing`. When optional models (e.g. `gemini-3.1-pro-preview`) vote `amend` or lack `best_within_constraints: true`, these should be **warnings**, not **failures**. If you see multiple blocked tasks with identical failures like:
- `best_within_constraints_missing:gemini-3.1-pro-preview`
- `unexpected_consulted_model:gemini-3.1-pro-preview`
- `missing_required_model_vote:mimo-v2.5-pro`

...check whether the gate code distinguishes `REQUIRED_RATIFICATION_MODELS` from `OPTIONAL_RATIFICATION_MODELS`. The per-vote checks (L6239-6243) must wrap optional models in `warnings.append()` not `failures.append()`. Fix location: `ratification_gate_result()` in `brain_task_orchestrator.py` around line 6226.

After fixing the gate, unblock affected tasks with:
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "<task_id>" --to pending --force \
  --actor "gate-fix:optional-model-handling" \
  --reason "Unblocked: fixed ratification gate to treat optional models as warnings not failures."
```

## Pitfall: mission envelope fields

Tasks that carry mission-envelope markers must include the full envelope. If `selfcheck` reports `mission_envelope_missing`, populate the required fields instead of disabling the check:
- `mission_schema_version`, `mission_id`, `mission_title`, `mission_objective`
- `mission_constraints`, `red_lines`, `non_goals`
- `evidence_refs`, `acceptance_criteria`, `dag_nodes`, `checkpoint_states`
- `permission_gates`, `handoff_artifacts`, `proof_artifacts`
- `rollback_signal`, `certification_status`, `ratification_artifact`

For structured ref fields use accepted prefixes, e.g. `artifact:/path/to/discussion_result.json` and `proof:...`.
