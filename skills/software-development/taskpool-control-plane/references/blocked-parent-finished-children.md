# Blocked Parents with Finished Children

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Blocked parents can already have finished convergence subtasks

Do not assume a blocked multimodel parent lacks decomposition work. Before creating more subtasks or re-diagnosing from scratch:
1. Search for `auto_subtask_parent: <parent-id>` in the task directory.
2. Inventory the existing `auto_subtask_axis` slices, typically:
   - `quota_observability`
   - `fallback_threshold`
   - `relay_ordering`
3. Check whether those subtasks are already `done` and whether any of them reached `multimodel_last_gate_status: PASS`.
4. If all convergence subtasks are finished but the parent remains `blocked`, treat the problem as an evidence-integration / parent-ratification issue, not a missing-subtask issue.
5. Auto-backfill the child evidence into the parent before deciding anything else.
   - Write/refresh a dedicated body section such as `## Auto-subtask Backfill` summarizing each child link, `auto_subtask_axis`, child status, and child multimodel gate/status.
   - Mirror the same relationship into structured frontmatter `evidence:` entries (`artifact:<child-note>`, `child-task:<id>:status:<status>`, `child-axis:<axis>:<id>`, plus child discussion/ratification artifacts when present).
6. Only reopen the parent to `pending` if the multimodel economy gate still allows another round.
   - If `task_multimodel_economy_gate(...).action == pause`, keep the parent `blocked` even after successful backfill.
   - Record a proof-log line that evidence was backfilled but the parent stayed blocked because pause requires human review or a more targeted evidence fix.

This avoids duplicating narrowing work and points the next step toward targeted evidence reintegration or human adjudication without accidentally re-dispatching pause-gated work.

### Proven repair pattern

1. Run `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`.
2. Split failures into buckets:
   - `done task missing evidence: <task>`
   - `unstructured evidence in <task>: <entry>`
   - any real safety errors such as invalid proof hashes
3. For `done task missing evidence`, inspect the task note before editing.
   - If `## Proof Log` / `## Final Handoff` already contain concrete verification detail, migrate that history into structured frontmatter `evidence:` entries.
   - Prefer one concise `proof:` summary entry over fabricating new command results.
   - Preserve the original body narrative; the migration should make existing proof machine-readable, not rewrite history.
4. For `unstructured evidence in ...`, convert ad-hoc tokens into accepted structured prefixes.
   - A durable pattern that worked here was converting multimodel state lines like `multimodel_gate:FAIL` into `classification:multimodel_gate=FAIL`.
   - If a legacy free-text `proof:` line is really pointing at an artifact, split it into `artifact:/abs/path` plus a concise `proof:` summary.
5. Re-run `proof-check --json`, then `evidence-spine --json`, then a real dispatch tick with `--autorun-step` if you need end-to-end confirmation.

### Guardrails

- Do not invent fresh test/build/browser results for already-closed historical tasks.
- Do not suppress proof failures in code when the safer fix is to structure evidence already present in the note.
- Treat `classification:` as structured evidence for machine-readable state labels; use it for taxonomy/status facts, not as a substitute for actual verification proof.
- If proof debt is historical and bounded, fix the notes first; only relax runtime gating when the debt truly cannot be repaired immediately.

### Historical artifact loss in blocked resolver

A proven failure mode is: dispatch tick already tolerates historical proof/evidence debt, but `blocked-resolve-step` still aborts the whole tick because a blocked task points at a pruned `multimodel_last_discussion_artifact` under `~/.hermes/tick-*/discussion_result.json`.

Key rule:
- Taxonomy enrichment for blocked-task diagnosis is **diagnostic only**.
- Missing historical discussion artifacts must be downgraded to a warning payload such as `taxonomy_warning`, not raised as a fatal control-plane error.
- Keep the task itself blocked when certification is still not PASS, but do **not** let missing historical artifacts freeze unrelated dispatchable tasks.

Patch targets that proved correct:
- In `brain_task_orchestrator.py`, inside `command_blocked_resolve_step()`, catch `SystemExit` from `load_discussion_artifact()` inside the taxonomy helper and continue with empty discussion data while preserving the missing-artifact message in the result payload.
- Apply the same fail-soft rule to `command_auto_split_non_convergence()`: if `load_discussion_artifact(parent)` raises because a historical `tick-*/discussion_result.json` was pruned, set `discussion = {}`, preserve `taxonomy_warning`, continue building fallback taxonomy/children from parent failure fields, and include `taxonomy_warning` in both proof log and JSON result. Verify with `py_compile` plus `auto-split-non-convergence --task <blocked-parent> --json`; expected result is `status=OK`, not a fatal missing-artifact exit.

### Parallel worker async default

- `brain_task_dispatch_tick.py --parallel-autorun` normally claims/handoffs a boundary-safe batch, then starts ordinary workers asynchronously via `agent_team_controller.py consume-claimed --background`. The tick should not wait for `hermes chat` workers. Use `agent_team_controller.py worker-jobs` to inspect durable jobs; use `--parallel-worker-foreground` only for debug/timeout-cleanup tests.
