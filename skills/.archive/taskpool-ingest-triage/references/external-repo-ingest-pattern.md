# External repo ingest pattern

Extracted from `/Users/charles/.hermes/skills/.archive/taskpool-ingest-triage/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

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
