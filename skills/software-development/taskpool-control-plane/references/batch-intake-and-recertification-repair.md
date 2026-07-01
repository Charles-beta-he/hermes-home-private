# Batch intake and recertification repair lessons

## External-source batch intake

When adding many external repo/video/social links to the local-brain taskpool:

1. Classify each source before writing: repo/docs/video/unknown-content, target surface, priority, evidence artifacts, red lines.
2. Use `add-repo-capability-absorption` for repo/video/source absorption tasks, but do **not** pass ordinary `add`-only flags such as `--workflow-stage` or `--completion-boundary`; this subcommand rejects them.
3. If a batch loop times out, assume partial writes happened. Do not rerun blindly.
   - Search task notes for each unique source URL/shortlink.
   - Count which tasks were actually created.
   - Check `multimodel-intervention-jobs --json`; `alive_count=0` means old claim files are only history.
4. A creation command with `--requires-multimodel` may immediately claim tasks into `running`/`review`. This is expected if the autorun/multimodel hook fires, but it must be read back.
5. For unknown or platform-gated video content, keep the task in `pending` or evidence stage with explicit OCR/transcript requirements. Do not invent the title/content if only a shortlink is known.
6. If an intake task is stuck `running` with `claimed_by=hermes-multimodel` and `multimodel-intervention-jobs --json` shows no alive job, release it with a reason like `stale hermes-multimodel claim after batch_intake_script_timeout; no alive multimodel job; release_to_pending_for_future_content_capture`.
7. Before dispatching newly-created Kanban cards, ensure each `ready` task has a real spawnable Hermes profile as `assignee`. A ready-but-unassigned card is not dispatchable; assign it to an existing profile (`hermes kanban assignees --json`) before expecting workers to run.
8. Match task skill hints to the assigned profile. If a worker crashes immediately with `Error: Unknown skill(s): ...`, treat it as a routing/config mismatch, not task failure: reassign to a profile that can load those skills (often `default`), add a comment/reason, `unblock`, and dispatch again. Read back events/runs afterward; a quick unblock may be picked up by the gateway dispatcher even if an immediate manual dispatch dry-run shows no spawn.
9. Verify after intake/dispatch:
   - `hermes kanban stats --json` shows ready/running/blocked counts.
   - `hermes kanban dispatch --dry-run --json` distinguishes `skipped_unassigned`, `skipped_nonspawnable`, per-profile caps, and spawnable work.
   - `hermes kanban show <task> --json` confirms assignee, status, latest events, and run history.
   - `hermes kanban log <task>` is checked for startup errors such as unknown skills.
   - `brain_task_orchestrator.py list --json` shows expected task count when the legacy brain mirror is involved.
   - `selfcheck --json` PASS.
   - `proof-check --json` PASS.
   - `boundary-check --json` PASS.
   - `v_state.py --json` remains HEALTHY. A score below 1.0 can be normal immediately after intake when new active/pending backlog lacks Kanban provenance; distinguish expected backlog from failures.

## Repair-child recertification after late degraded writeback

If a task was already legitimately `done` but a later autorun/multimodel closeout round moves it back to `blocked`:

1. Treat this as a real governance boundary first; do not force-close.
2. Compare the earlier passing artifact with the later degraded artifact:
   - `status`, `truth_assessment`, `fanout_certification`, `planner_patch_summary`, `issue_ledger`, `remaining_risks`, votes, and evidence requests.
3. If the later artifact has `truth_status=grounded` / `evidence_coverage=1.0` and the blocker is framing/fanout/no-action ambiguity rather than contradictory implementation evidence, repair the **state packet** with claim-linked evidence and rerun governed certification.
4. Do not edit model outputs, lower quorum, or relabel a degraded artifact as certified.
5. Include in the new state packet:
   - parent closeout proof and hash;
   - prior certified artifact and hash;
   - later degraded artifact and its exact blocker;
   - current control-plane PASS evidence;
   - explicit scope: no-action evidence reconciliation, not new implementation.
6. Rerun `multimodel-intervention-step` normally. Only transition to `done` after gate `PASS` / decision `LOOP_DONE`.
7. If Kanban projection still shows a blocked mirror for a source-done task, complete the mirror with metadata explaining `blocked_projection_for_done_source` rather than editing the source state by hand.
