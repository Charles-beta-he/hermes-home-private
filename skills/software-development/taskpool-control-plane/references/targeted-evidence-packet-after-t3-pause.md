# Targeted evidence packet after T3 pause

Use when a blocked parent has exhausted T3 / multimodel rounds and the resolver says it requires human review or a targeted evidence fix, especially after children are complete but parent certification is still paused.

## Symptom

- `blocked-resolve-step --task <parent> --json` returns `kept_blocked_count=1`.
- Reason resembles: `task has N failed T3 rounds (max=5); requires human review or targeted evidence fix`.
- Parent aggregation is clean:
  - `ready_for_parent=true`
  - `open_children=[]`
  - `missing_children=[]`
  - `stale_evidence_count=0`
- `multimodel-intervention-dry-run` returns a paused plan only:
  - `intervention_required=false`
  - `actionable_count=0`
  - `paused_count=1`
  - `economy_gate.action=pause`
- Optional additional clue: `taxonomy_artifact_warning` says a historical `discussion_result.json` is missing/pruned.

## Safe procedure

1. Snapshot the live state, do not infer from old proof logs:
   ```bash
   python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --task '<parent-id>' --json
   HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-dry-run --task '<parent-id>' --json
   python3 ~/.hermes/scripts/taskpool_parent_evidence_aggregator.py --task '<parent-id>' --json
   ```

2. If the parent aggregation is clean but certification remains paused, create a targeted evidence packet that narrows the blocker. The packet should record:
   - parent id and current status;
   - child count/done count;
   - open/missing children;
   - stale evidence count;
   - axis summary;
   - exact remaining blocker;
   - artifact inventory for the task's required acceptance paths and the latest discussion artifact;
   - explicit statement that the packet is not completion authority.

3. Attach structured references to the parent task note, not as fake completion proof:
   - `artifact:<packet.md>`
   - `artifact:<packet.json>`
   - `proof:sha256:<packet-json-hash>`
   - `command:targeted_evidence_fix_readback ... PASS ...`
   - `proof:targeted_evidence_fix_<axis>_<summary>`

4. Verify immediately:
   ```bash
   python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py eligibility-check --task '<parent-id>' --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --task '<parent-id>' --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 8 --lane all --json
   python3 ~/.hermes/scripts/agent_team_controller.py status --json
   python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json
   ```

5. If the resolver remains paused, stop at the boundary. The remaining legal choices are:
   - restore the missing/pruned discussion or acceptance artifacts and rerun resolver/ratification;
   - get human acceptance that the new targeted evidence packet and current ledger are sufficient substitute readback, then authorize one scoped parent ratification refresh;
   - if the original provider blocker is fixed later, record a fresh provider-recovered targeted-evidence readback newer than `multimodel_last_checked_at` so the bounded rerun allowance is not accidentally reused from an already-consumed packet;
   - keep the parent blocked.

6. After the scoped refresh, always separate outcomes:
   - Provider/runtime blocker: no `discussion_result.json`, missing required model, provider hard gate, or partial checkpoint only. Keep blocked and produce a provider-gate packet.
   - Content disagreement blocker: `discussion_result.json` exists but `ratification-gate` returns FAIL/continue_loop. Keep blocked, attach the discussion/gate readback, and split unresolved severity issues or global-router mutations into separate evidence tasks instead of rerunning the same parent refresh.
   - Certification pass: only proceed to lifecycle review when the ratification gate returns PASS/LOOP_DONE with required participants and no unresolved high-severity issues.

## Pitfalls

- Do not run another `multimodel-intervention-step` simply because the user asked to "推进 blocked" when the dry-run shows only `paused_plans`. The dry-run is the gate.
- Do not mark the parent `done` from child convergence alone; finished children are evidence inputs, not parent certification.
- Do not ordinary-worker redispatch the parent after the packet if `dispatchable_count=0` and exact eligibility still says `task_not_dispatchable` or `allowlist_miss`.
- A missing historical `discussion_result.json` should be captured as an artifact-inventory gap, not papered over with invented discussion content.
- Evidence-only commits can be classified by the local pre-commit gate as T3/lifecycle-write if they are tied to taskpool certification. If the hook blocks for missing `task_record`, `proof_log`, or `lifecycle_readback`, leave the evidence packet on disk and attached to the task note, or provide the missing gate evidence first; do not bypass the hook just to commit the packet.

## Expected outcome

A successful targeted evidence packet does not necessarily unblock dispatch. It should make the blocker sharper: from "maybe stale children / missing child work" to "parent certification/human review/artifact restoration required." That is progress, even when `resolved_count=0` remains correct.
