---
name: taskpool-ingest-triage
description: Use when adding external links, notes, repo analyses, or decomposed implementation tasks into the taskpool; enforces pre-ingest triage, priority stratification, dependency capture, and execution-order metadata at creation time.
---

# Taskpool Ingest Triage

## Overview

Use when adding external links, notes, repo analyses, or decomposed implementation tasks into the taskpool; enforces pre-ingest triage, priority stratification, dependency capture, and execution-order metadata at creation time. This skill is maintained as a `pipeline`-shaped contract: it should guide ordered multi-stage work with gates, evidence, retries, and closure states without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `taskpool-ingest-triage` and requires ordered multi-stage work with gates, evidence, retries, and closure states.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

## Blocked multi-model workflow diagnostics

When asked why taskpool/workflow items are `blocked` or whether they will automatically complete, use `references/blocked-multimodel-diagnostics.md`.

For repo/article/screenshot intake that mentions multimodel analysis, use `references/multimodel-taskpool-contracts.md`: multimodel means real external model participation, not simulated roles; task creation may mark `requires_multimodel` automatically, but actual external calls still require an explicit execution gate.

## Multimodel intake semantics

When adding external repos/articles/links or interpreting conversational requests for "多模型思考 / 多模型分析 / 多模型认证 / consult_models", multimodel means real external model participation, not single-model multi-role simulation. Preserve true intent on taskpool items with `requires_multimodel`, `multimodel_reason`, `expected_participants`, `truth_gate`, and `evidence_bundle`; keep expensive execution fail-closed until explicitly authorized. See `references/multimodel-intake-semantics.md`.
When asked why the pool has active work but no task is currently in progress, use `references/taskpool-autostart-and-gating.md`.

When users say there is "no task in progress" or ask why nothing is actively running, use `references/no-in-progress-diagnosis.md`. The durable pattern is that the pool may still contain active `pending`/`blocked` work while dispatch tick is failing governance gates (especially proof/evidence checks), so verify list/dashboard state, dynamic-runner logs, direct tick output, eligibility, and manual autorun handoff before concluding the pool is empty. Key rule: inspect `brain_task_orchestrator.py list --include-done --json` (`rows`), then distinguish ordinary dependency/claim blocks from multi-model ratification-gate blocks. For `dispatchable=false` + `multimodel_status=not_certified`, do not promise automatic `done`; verify dynamic worker/cron intervention and report the exact missing votes, consensus failures, or constrained-best gaps.

Use this when:
- The user sends repo/article links and wants them added to the taskpool
- A parent task is being decomposed into child tasks
- Work should enter the pool as a governed execution unit rather than a raw inbox item
- The user wants the taskpool to stay independent from later ad hoc re-triage
- The user asks why the pool has active tasks but nothing is in progress, or why no task auto-advanced to `claimed`/`running`

## Core rule

Do not treat task creation as raw capture.
Before or during `brain_task_orchestrator.py add`, convert the input into a governed task record with:
- P1/P2/P3 priority already decided
- dependency / sequencing intent already decided
- architecture target already decided
- multimodel triage rationale already decided for high-leverage items
- parallel boundary and acceptance boundary already stated when decomposition is involved

## Required ingest sequence

1. Classify the incoming work
   - External repo/article/reference to analyze
   - Parent task being split into child tasks
   - Direct implementation / audit task
   - Advisory / observation-only candidate

2. Run pre-ingest triage before formal add
   For external links and strategy-facing tasks, determine before creation:
   - Strategic leverage on Hermes/taskpool/control-plane
   - Near-term executability
   - Architectural landing zone
   - Overlap with existing tasks
   - Whether the item is true P1, normal P2, or reserve P3

3. Decide P1/P2/P3 at creation time
   Use a simple gate:
   - P1: directly changes core control-plane, taskpool, permission, context, prompt assembly, orchestration, recoverability, or another strong lever on overall completion/stability/cost
   - P2: clearly useful and actionable, but not first-batch leverage
   - P3: backlog/reserve/observation value; worth keeping but not immediate

4. Capture execution structure at creation time
   When creating decomposed tasks, decide and encode:
   - Which task must happen first
   - Which tasks can run in parallel
   - Which tasks are blocked by earlier outputs
   - Which task is packet/schema/protocol first and which is automation/state-machine later

5. Use workflow-contract fields intentionally
   At minimum review/populate these frontmatter fields when applicable:
   - `workflow_contract`
   - `required_authority`
   - `permission_tier`
   - `completion_gate`
   - `parallel_boundary`
   - `architecture_target`
   - concepts / capability_delta / anti_drift_check / acceptance_evidence

6. Add tasks only after the above decisions exist
   The pool should store governed tasks, not raw materials.

## Decomposition rule

When splitting one topic into multiple tasks, prefer this pattern:
- schema/packet definition first
- protocol/integration second
- automation/control-flow third

This avoids creating downstream tasks whose inputs are undefined.

Example from budget-handoff work:
1. Define continuation packet schema
2. Define `/new` + `prefill_messages` resume protocol
3. Define automatic handoff / fallback state machine

### Tutorial / catalog repo category-split rule

When the source is a tutorial repo, curated toolbox, or catalog that already groups items into a few durable application areas, do **not** mechanically create one narrow task per listed item by default.

Prefer a governed category split:
- create one task per durable category / scenario lane
- keep each task focused on the mechanisms shared by that category
- mention the enumerated items in `evidence_bundle`, `objective`, or `capability_delta`
- reserve per-item tasks for cases where one item is clearly high leverage, architecturally distinct, or likely to need an independent execution lane later

Good default examples:
- efficiency tools / research tools
- product-development workflow tools
- content-creation tools
- daily-report ingestion / source-quality upgrades

This keeps taskpool intake aligned to class-level absorption work instead of exploding into 10+ one-shot repo notes with overlapping acceptance scopes.

## Multimodel triage guidance

For external repo/article ingest or high-impact architecture work:
- Perform fixed multimodel triage before add, not after add
- Record the result in the task framing/rationale or supporting evidence
- Treat “triggered multimodel” and “passed/converged multimodel” as different states; do not mistake trigger statistics for completed analysis

### External repo ingest pattern

For GitHub repos, do a minimum evidence pass *before* `add`:
- fetch repo metadata (description, language, stars/forks/issues, topics)
- read README or equivalent project positioning text
- search the taskpool for existing mentions/duplicates
- produce three explicit judgments before creation:
  1. priority tier (P1/P2/P3) and why
  2. Hermes architectural landing zone (`local-brain` / `taskpool` / `control-plane` / other) and why
  3. anti-drift / acceptance / boundary constraints so the task does not turn into a generic industry survey

When the repo is a coding-agent / harness / orchestration project, prefer framing the created task around **what Hermes should absorb** (gap map, leverage points, smallest closure slice, execution order) instead of a broad repo summary.

#### Same-domain repo overlap rule

If the new repo lands in the same mechanism class as an already-created task (for example: another memory layer, another agent orchestration harness, another skill/prompt governance system), do **not** create a second generic “analyze this repo” task with interchangeable wording.

Required comparison pass before `add`:
- identify the closest existing repo-analysis task in the same mechanism class
- state the **net-new mechanisms** this repo adds relative to that earlier task
- encode the title/objective around those deltas instead of broad repo analysis
- explicitly ban repeating the prior generic survey in `anti_drift_check`

Good framing examples:
- not: “analyze another memory repo”
- yes: “compare shared memory server / hook capture / hybrid retrieval deltas vs existing claude-mem analysis”
- not: “analyze another multi-agent framework”
- yes: “extract specialist orchestration / graceful degradation / deliverable-closure deltas vs existing orchestration tasks”

This keeps the pool from accumulating parallel repo-reading tasks that all restate the same architecture themes.

#### Exact-repo duplicate rule

If taskpool search already finds the **same repository/source** (same GitHub owner/repo or obviously identical canonical subject), do **not** create another task just because the user pasted the link again or re-described the same project in different words.

Required handling:
- read back the existing canonical task before deciding anything
- report its path plus the key governance fields that matter now (`status`, `priority`, `architecture_target`, and if useful `project`)
- treat the default action as **no new task created**
- only create a follow-on task when the user is actually introducing a clearly different incremental angle that the existing task does not already encode
- when you do create such a follow-on, title it as a **second-pass / incremental absorption** task and explicitly ban re-summarizing the same repo in `anti_drift_check`
- for a completed canonical task, also append a short `Supplemental Notes` entry to the original task pointing at the follow-on, so future duplicate checks see why the new task exists and do not re-open the old generic analysis

Interpretation rule:
- “same repo, same angle” -> reject as duplicate and point to the canonical task
- “same repo, new mechanism slice” -> create a narrowly-scoped incremental task only if the delta is real and durable
- “same repo, user adds a moat / layer / mechanism absent from a done task” -> create a second-pass task scoped to that mechanism, mark it as incremental, and preserve the original done task as canonical context

Operational pitfall:
- `brain_task_orchestrator.py add` may trigger event hooks or multimodel intervention and outlive a short caller timeout. If the add call times out, search the taskpool for the intended title/metadata before retrying; if the task exists, verify its frontmatter/status instead of creating a duplicate.

#### Company-level multi-agent control-plane repo rule

When the repo is not merely an agent runtime but a **company-level control plane** for many agents (for example: org chart, goals, tickets, heartbeats, budgets, approvals, multi-company isolation, dashboard supervision), do not file it as a generic “multi-agent” task.

Required framing before `add`:
- compare it against existing Hermes tasks on `delegate_task`, subagent orchestration, and parallel-boundary governance
- identify the control-plane deltas explicitly: `org chart`, `goal ancestry`, `heartbeat scheduling`, `budget hard-stop`, `approval / rollback governance`, `multi-company isolation`, `agent-ops dashboard`, `portable company templates`
- prefer `architecture_target: taskpool` or `control-plane` unless the evidence clearly shows the main delta belongs somewhere else
- encode in `anti_drift_check` that the task must not degrade into “AI company / autonomous company” concept narration or ethics-only commentary
- require the output to separate **absorbing the mechanism** from **endorsing the product story**

Default priority guidance:
- `P2` when the repo contributes durable control-plane mechanisms but is not an immediate P1 blocker/fix
- escalate to `P1` only when the repo directly informs an already-active core control-plane defect or committed implementation slice

### External article / essay ingest pattern

For strategy essays, blog posts, and architecture opinion pieces, do not add a raw “analyze this article” task without first separating **theme overlap** from **incremental mechanism gain**.

Minimum evidence pass before `add`:
- read the article and extract the concrete mechanisms, not just the headline thesis
- search the taskpool for existing prompt / agent / memory / orchestration tasks that already cover the same theme
- decide whether the article is:
  1. a duplicate framing of an existing P1 objective,
  2. a supporting reference for an existing task, or
  3. a true incremental task because it introduces a new mechanism Hermes does not yet track

When overlap exists, prefer this rule:
- keep the existing P1 canonical task unchanged
- add a **P2 incremental absorption task** only if the article contributes new mechanisms, boundaries, or architecture implications
- explicitly state the boundary: what belongs to prompt governance vs skill-graph vs local-brain / eval / retrieval, so the new task does not become a duplicate prompt-governance note

If the source itself is the same as an already-created or already-completed task, do **not** create a second generic “analyze/read this article” task. First read the prior task/evaluation artifact and decide whether the new request is actually:
1. a duplicate that should be rejected,
2. a continuation / second-pass deep read that focuses on still-unlanded mechanisms, or
3. an execution follow-up that should be framed around concrete governance patches rather than article reading.

For these repeat-source cases, the new task title/objective should encode the incremental angle explicitly (for example: second-pass deep read, execution landing, regression-gate extraction, progressive-loading audit), and the anti-drift check should explicitly ban re-summarizing the same article.

Good article-ingest framing is: “what should Hermes absorb, where should it land, what is net-new, and in what order should it be implemented?” not “summarize why this article is interesting.”

### Add-command return-code pitfall

If `brain_task_orchestrator.py add` returns an event-hook nonzero such as `returncode=2`, do not assume the task failed to enter the pool. Verify the actual result payload and task note existence first. Current add output includes `created_ok`, `message`, `warnings`, and `hook_summary`: trust `created_ok=true` for task creation, then inspect `hook_summary.nonfatal` / `event_hook.log` separately for follow-up hook or autorun issues. If the task file exists and the add payload is `status=OK`, treat it as an ingest success with hook noise, not a missing task.

### Add-command list-field quoting pitfall

When using `brain_task_orchestrator.py add` with list-like frontmatter fields such as `dependency_order`, be careful not to double-wrap the value through shell quoting.

Durable rule:
- prefer the simplest accepted form for `--dependency-order` rather than passing a pre-escaped JSON array inside another quoted array
- after creation, always read back the created task's frontmatter and verify fields like `dependency_order`, `parallel_boundary`, and other structured governance fields rendered as intended
- if a field lands as a nested stringified array (for example `dependency_order: ["[\"step1 ...\"]"]`), patch it immediately instead of leaving malformed governance metadata in the pool

Why this matters:
- malformed `dependency_order` quietly degrades readability and downstream dispatch/governance quality
- this is easy to miss because `add` still returns `status: OK`

Operational pattern:
1. run `add --json`
2. verify created path/frontmatter
3. patch malformed structured fields immediately before finishing the ingest report

### Add-command metadata gate

Some local installs enforce richer ingest metadata than the basic `add --help` output makes obvious. In practice, task creation can fail closed unless `priority_layer`, `dependency_order`, and `multimodel_triage_result` are populated for governed intake work.

Operational rule:
- for external repo/article/tutorial ingest, always provide all three fields
- for internal evolution tasks (for example report->task automation, source-quality upgrades), still provide `multimodel_triage_result` explicitly when the queue expects governed triage metadata, even if the task does not need full external-repo multimodel contract fields
- if `brain_task_orchestrator.py add` errors with `missing=[...]`, treat that as a schema-discovery signal and immediately retry with the missing governance fields rather than downgrading the task framing

This avoids false negatives where a well-framed task is rejected only because one required governance field was omitted.

## References

- `references/multimodel-blocked-resolution.md` — repair pattern for tasks that remain `blocked` after multimodel certification passes because stale failed `evidence:` entries violate proof-gate shape.
- `references/non-convergence-auto-narrowing.md` — when a task is blocked by multimodel `loop_non_convergence`, preserve the parent objective and create a narrowed precondition child task instead of rewriting the parent into an easier but drifted target.

## Non-convergence blocked-task split rule

When a high-leverage task is `blocked` with multimodel signals like `multimodel_status=not_certified`, `multimodel_last_decision=CONTINUE_LOOP`, `agreement_below_threshold:*`, or `certification_intent=unresolved_noop_vs_change`, do **not** solve it by silently rewriting the parent task into an easier version.

Use this recovery pattern instead:
1. Keep the parent task as the canonical objective.
2. Extract the disagreement axis from the discussion artifact: typically `framing`, `approach`, `implementation_order`, or `noop_vs_change`.
3. Create one or more **precondition child tasks** whose sole purpose is to make the parent ratifiable again.
4. Record in the parent task's `Blockers / Confusions` that the block is `loop_non_convergence` and that the new child task(s) are front-loaded dependencies.
5. Add a `Proof Log` note in the parent that the unblock child task was created and should be executed before resuming the parent.
6. Narrow child tasks by axis, not by convenience: e.g. `quota observability`, `fallback threshold semantics`, `continuation packet / relay ordering`, or `patch normalization`.
7. Re-run ratification only after the child task produces a narrowed brief or evidence packet.

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

### Closure-loop escalation rule

When `loop_non_convergence` persists, treat it as a lifecycle problem, not just a split problem. The expected closure loop is:
1. `blocked-resolve-step` detects `loop_non_convergence` on a blocked parent and triggers `auto-split-non-convergence` when no narrowed children exist yet.
2. Child tasks must persist `auto_subtask_parent` and `auto_subtask_issue_ids` so the parent can be recovered without goal drift.
3. `reconcile` and `auto-subtask-sync --write` are the canonical parent-refresh paths; once all narrowed children are `done`, a blocked parent should automatically reopen to `pending`.
4. `blocked-resolve-step` should then report either `await_auto_subtasks` or `auto_subtask_parent_reopened` rather than leaving the parent in an ambiguous blocked state.

### Taxonomy-first narrowing rule

If the latest discussion artifact has weak or empty `issue_ledger`, do not fall back to a vague framing-only split. First derive a multimodel failure taxonomy from discussion failures and use it to recommend split axes. Durable mapping from this session:
- `agreement_low` -> `relay_ordering`
- `criteria_missing` and `loop_non_convergence` -> `fallback_threshold`
- `quota_unobservable` / `evidence_missing` / `no_claims` -> `quota_observability` (and sometimes `framing`)
- `final_design_missing` / provider parse problems -> `patch_normalization`
- `model_vote_missing` / `vote_reject` -> `framing`

Expected automation behavior:
- write parent-level `auto_subtask_taxonomy_axes`
- return `taxonomy_axes` and `axis_rationale` from `auto-split-non-convergence --json`
- write task-level `multimodel_recommended_axes` during PUA-loop result writeback so later split/reconcile passes reuse the same semantics

## Pitfalls

- Fixing convergence by changing the parent's goal instead of preserving it and splitting out a prerequisite child task.
- Creating a vague 'follow-up analysis' task that mixes multiple disagreement axes; split by one axis per child when possible.
- Treating `loop_non_convergence` as a scheduler failure; it is usually an evidence/framing failure.
- Re-running full multimodel discussion without first extracting the disagreement taxonomy from the last discussion artifact.

## Pitfalls

- Adding everything as P2 and promising to reorder later
- Creating child tasks without dependency/order semantics
- Treating taskpool as an inbox instead of a governed queue
- Leaving `parallel_boundary` blank on obviously serial vs parallelizable decompositions
- Deferring multimodel priority analysis until after the task is already in the pool
- Assuming a workflow contract exists means the ingest path already enforces it

## Verification

Before finishing, verify:
- Priority was decided before/at add time
- Child tasks have a clear recommended execution order
- Any P1 architecture task has a stated reason it is P1
- The created task text reflects dependency/parallel intent where relevant
- If the user challenged the ingest workflow, the fix was captured in the task formulation rather than only in chat

## Reference

See `references/taskpool-ingest-checklist.md` for a concise pre-add checklist and dependency-order heuristics.

## Taskpool Cleanup & Deduplication

When the task pool accumulates duplicates or stale tasks:

1. **Deduplicate by title**: Keep most recent, delete older duplicates with same title
2. **Archive stale subtasks**: Convergence subtasks (title contains 细化) whose parents are done → archived
3. **Archive low-value research**: Generic repo analysis that overlaps with completed tasks → archived
4. **Regenerate dashboard**: `python3 scripts/brain_task_orchestrator.py dashboard --write`

Pitfall: Kanban titles may differ from brain filenames — use LIKE patterns, not exact match.
