# Ratification repair closeout: allowlist, read-compatible packet gates, and safe evidence binding

Use this reference when a taskpool review-gap repair child or parent loops in `retry`/`review` after evidence appears complete, especially for `missing_multimodel_certification`.

## Reusable pattern

1. **Classify the blocker before rerunning workers.** If `agent_team_controller consume-claimed` is blocked by human-escape or worker safety, do not keep claim/release cycling. Switch to deterministic evidence repair.
2. **Verify the artifact independently.** For a local ratification JSON, verify at least:
   - schema is expected;
   - parent/repair-child task ids match the intended tasks;
   - certification result is PASS;
   - loop is done (`decision/loop_status=LOOP_DONE` or `loop_done=true`);
   - certification status is certified;
   - vote is approve where present;
   - red lines are safe;
   - acceptance criteria are covered;
   - sha256 is recorded.
3. **Bind evidence without force-done.** Attach the verified artifact/sha/check result to the task evidence and move via legal lifecycle edges (`pending -> claimed -> running -> review`) if a review gate must inspect it. Do not skip straight to `review` from `pending`, and do not mark `done` manually.
4. **Check the allowlist only for exact scope.** If `auto-close-review` fails with `allowlist_miss`, add only the exact task ids (or a narrowly scoped existing project key when appropriate) to `~/.hermes/state/multimodel_intervention_allowlist.json`, and make a timestamped backup before editing.
5. **Prefer read-compatible gate fixes for recurring packet shapes.** If a legitimate historical/repair packet shape is target-bound and deterministic but not accepted by `task_multimodel_passed()`, add narrowly scoped read-compat support plus a focused regression test. Do not weaken the strict `ratification-gate` for new discussion artifacts.
6. **Run closeout and read back.** Re-run `auto-close-review`, then `reconcile`, `selfcheck`, `proof-check`, and `taskpool_watch_report`. If closeout now reaches a different blocker (for example browser/UI surface proof), stop and classify that blocker separately.

## Packet-shape pitfall: `multimodel_ratification_v1`

Some repair workers write compact packets like:

```json
{
  "schema": "multimodel_ratification_v1",
  "parent_task_id": "...",
  "repair_child_task_id": "...",
  "certification_result": "PASS",
  "loop_done": true,
  "certification_status": "certified",
  "vote": "approve",
  "truth_gate": {"can_certify_truth": true},
  "no_red_line_violations": true,
  "acceptance_criteria_coverage": [{"status": "covered"}]
}
```

Older gates may only recognize `status=PASS` plus `decision/loop_status=LOOP_DONE`. The safe fix is to map `certification_result` to PASS and `loop_done=true` to LOOP_DONE only inside the legacy/read-compatible packet path, and require target binding via `parent_task_id` or `repair_child_task_id`.

## Anti-conditions

- Do not record a transient provider failure as a durable rule; capture only the gate/verification pattern.
- Do not add broad project allowlist entries when exact task ids are sufficient.
- Do not treat advisory or degraded multimodel output as certification authority.
- Do not clear historical autorun proof debt without append-only proof log/readback evidence.
- Do not turn a browser/UI closeout proof blocker into a multimodel issue; it is a separate gate.

## Minimal verification checklist

- Focused regression for the accepted packet shape passes.
- `py_compile` passes for changed scripts/tests.
- `selfcheck --json` returns PASS.
- `proof-check --json` returns PASS; warning debt may remain if unrelated historical proof debt is present.
- `taskpool_watch_report.py --json` returns normally.
- Scoped git status contains only intended files before commit.
