# Automation support

Extracted from `/Users/charles/.hermes/skills/.archive/taskpool-ingest-triage/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Automation support

If the orchestrator has the `auto-split-non-convergence` command, prefer using it before hand-authoring child tasks.

When explaining taskpool decomposition or blocked-task split behavior, distinguish three layers explicitly:
- governed ingest-time decomposition (always part of the workflow when one topic should become multiple tasks)
- parent/child blocked-task semantics (`auto_subtask_*` fields, reopen/sync behavior)
- productized CLI automation for generating those subtasks

Do not imply the third layer exists just because the first two do. Verify the currently installed `brain_task_orchestrator.py --help` output before claiming there is a live `auto-split-non-convergence` command or other automatic split entrypoint. If the command is absent, report that decomposition exists as a workflow/pattern but may still require explicit hand-authored child tasks in this local install.

Operational notes from the first implementation:
- Read the actual discussion artifact shape before classifying splits. In real `discussion_result.json` files, the decisive fields may live under `final_design.planner_patch_summary`, `final_design.merge_info`, and `final_design.quota_snapshot`, not only at the top level.
- Good split triggers include:
  - `agreement_matrix` dimensions below threshold
  - `final_design.merge_info.minority_patches` containing `quota`, `threshold`, or `relay` patches
  - `final_design.planner_patch_summary.certification_intent=unresolved_noop_vs_change`
  - low-confidence or `unknown`/`unobservable` entries inside `quota_snapshot`
  - unresolved `issue_ledger` IDs
- The automation must be **parent-preserving and idempotent**:
  - preserve the parent objective unchanged
  - write `auto_subtask_children` / `auto_subtask_kind` on the parent
  - update parent `Proof Log` and `Blockers / Confusions`
  - on rerun, create only missing subtasks instead of duplicating existing ones
- For budget-handoff style failures, the default three-way split is:
  1. quota observability
  2. fallback threshold semantics
  3. relay ordering

See `references/non-convergence-auto-narrowing.md` for the concrete artifact layout and command behavior.
See also `references/non-convergence-closure-loop.md` for the parent-reopen closure loop, taxonomy-driven axis selection, and blocked-resolve-step integration.
