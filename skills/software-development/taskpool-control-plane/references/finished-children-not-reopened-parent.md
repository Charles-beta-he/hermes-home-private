# Finished Children Do Not Equal Reopened Parent

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Finished children do not equal a reopened parent

A recurring false-positive is: you successfully claim and finish every newly split convergence child, `auto-subtask-sync` reports `ready: true` with `open_children: []`, but `next --json` still says there is no dispatchable work and `list --json` still shows only the blocked parents.

### Built-in targeted-evidence refresh may reveal a *new* missing child axis

Current control-plane behavior is now safer and more automatic than the old manual recipe:
1. `auto-split-non-convergence` preserves the full taxonomy axis set instead of truncating to three children.
2. When all convergence children are done and the multimodel economy gate still allows a new round, `blocked-resolve-step` / `reconcile` reopen the parent with `## Auto-subtask Backfill` evidence.
3. The next `multimodel-intervention-dry-run` / `multimodel-intervention-step` for that parent switches into a built-in `blocked_parent_targeted_evidence` refresh mode.
4. That mode freezes the original parent objective, injects finished child notes/artifacts as evidence, and reruns parent ratification through the normal `write_multimodel_result_to_task(...)` path.
5. If the refreshed parent still FAILs, re-run `auto-split-non-convergence`; a newly surfaced axis is legitimate only when the refreshed taxonomy/evidence points to coverage the previous child set never had.

Interpretation rule:
- This is not "more random decomposition".
- It is valid when the refreshed parent discussion gives a fresh unresolved ledger / taxonomy that the previous child set never covered.
- The goal is to restore dispatchability safely without shrinking the frozen parent objective.

#### Updated pitfall: verify axis coverage, not just child count

The old three-axis cap is gone, so the durable check is now coverage rather than count.

When a refreshed parent still FAILs:
1. Compare the new FAIL taxonomy (`recommended_axes`, unresolved issue ledger, vote reasons) against the actual `auto_subtask_axis` children.
2. Confirm the newly required axis is truly absent or materially under-evidenced before creating more decomposition.
3. Re-run `auto-subtask-sync --write`, `next --json`, and `list --json` to verify whether the pool now exposes a new dispatchable convergence child.

See `references/manual-targeted-evidence-refresh.md` for the historical failure signature and the explicit `--claim` / `--evidence-json` requirement; prefer the built-in control-plane path first.

Interpretation rule:
- Child closeout proves the narrowed axes were documented and accepted.
- It does **not** by itself refresh the blocked parent's multimodel certification state.
- If the parent still shows `multimodel_last_gate_status: FAIL`, `multimodel_last_decision: CONTINUE_LOOP`, or stale `multimodel_last_failures`, the remaining blocker is parent-level ratification/framing refresh, not missing child execution.

Use this sequence after child closeout:
1. Finish the child tasks and verify they are no longer open.
2. Run `auto-subtask-sync` for each parent.
3. Run `blocked-resolve-step --json`, then `next --json` and `list --json`.
4. If `open_children: []` / `missing_children: []` but the parent remains blocked, stop creating more child slices.
5. Reclassify the next step as one of:
   - refresh parent multimodel discussion / certification artifact,
   - integrate the child narrowed briefs into a new parent framing pass,
   - or target the specific remaining parent failure axes (often `framing` after threshold / relay / observability slices are already done).

Pitfall:
- Do **not** report progress as "new dispatchable tasks created" just because narrowed child notes were generated and later closed. Verify with `next --json`; if it still returns `next: null`, the pool has advanced evidence but not dispatchability.
