# Taskpool blocked certification rebuild

Use this when a taskpool task is blocked because `multimodel_last_discussion_artifact` is missing, an old `tick-*` directory was pruned, or a prior T3 loop needs to be rebuilt.

## Status separation

Do not collapse these statuses:

- fanout quorum / planner success count;
- truth gate (`truth_status`, `can_certify_truth`, `evidence_coverage`);
- final discussion certification (`status`, votes, `best_within_constraints`, unresolved severity >= 3 issues);
- lifecycle writeback.

`fanout_quorum_met`, `truth_status=grounded`, or `evidence_coverage=1.0` can corroborate evidence, but they are not full certification unless the required participant approvals and final manifest also pass.

## Rebuild steps

1. Read the canonical task note frontmatter/body and capture:
   - `multimodel_last_state_path`;
   - `multimodel_last_discussion_artifact`;
   - `multimodel_last_failures`;
   - latest lifecycle events.
2. Inspect the last discussion artifact and any earlier passing artifact for:
   - `agreement_matrix`;
   - `truth_assessment`;
   - `fanout_certification`;
   - `planner_patch_summary`;
   - `issue_ledger` / `remaining_risks`;
   - model votes and `best_within_constraints`.
3. If the failure is caused by missing source records, search for the referenced `source_hash` across `~/.hermes`, tick dirs, logs, and task notes.
4. If the source cannot be recovered but the later artifact says truth is grounded and the blocker is no-action/framing/fanout ambiguity, do not relabel the degraded artifact. Instead rebuild the state packet with explicit claim-linked evidence and rerun certification.
5. The rebuilt state packet should include:
   - narrow question/scope (e.g. no-action repair-child evidence reconciliation);
   - acceptance criteria matching that scope;
   - claim-linked evidence with paths and hashes;
   - the prior certified artifact and the later degraded artifact, both described accurately;
   - constraints forbidding quorum weakening, fabricated proof, or direct lifecycle bypass.
6. Rerun the governed path:

```bash
HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-step --task '<task-id>' --json
```

7. Only after gate `PASS` / decision `LOOP_DONE`, use normal lifecycle transition to `done` with evidence. Do not use force unless the lifecycle model explicitly requires it and the human has authorized the exact bypass.

## Anti-patterns

- Editing `discussion_result.json` to change model votes.
- Counting a degraded artifact as certified because its truth gate is grounded.
- Lowering quorum thresholds to clear one task.
- Closing from model agreement without artifact paths/hashes and control-plane readback.
