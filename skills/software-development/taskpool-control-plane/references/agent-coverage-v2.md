# Agent/Kanban Coverage v2

Use this when a user asks for Kanban/agents coverage, asks to drive coverage above a threshold, or when a previous coverage report looks green while no work is running.

## Problem this pattern prevents

The old coverage interpretation can false-green when `ready=0`: `kanban_ready_spawnability` may be 1.0 because the denominator is empty, while the actual system has a blocked backlog, stale brain-mirror projections, or missing provenance.

Treat `ready=0` as a state classification problem, not an automatic pass.

## v2 metric shape

Report a structured `agent_coverage_v2` block with:

- `profile_coverage`: referenced assignees/profiles exist and are spawnable.
- `flow_coverage`: ready work can be pulled, or blocked/idle state is explicitly classified.
- `projection_coverage`: Kanban projection status is aligned with canonical brain/source status.
- `provenance_coverage`: active brain notes have real Kanban/workspace/run refs or an explicit projection exemption.
- `blockage_coverage`: blocked cards carry enough source/workspace/blocker structure to audit or unblock.

Useful states:

- `flow_active`: ready > 0 and spawnable > 0.
- `flow_profile_blocked`: ready > 0 but ready tasks are nonspawnable.
- `flow_blocked_backlog`: ready = 0, dispatchable = 0, blocked > 0.
- `flow_idle_clean`: ready = 0, dispatchable = 0, blocked = 0.

## Score caps

Apply caps before reporting a healthy score:

- Stale projection exists -> cap at 0.75.
- Active provenance below 0.5 -> cap at 0.75.
- Blocked backlog exists but blocked items are not structured -> cap at 0.75.

This keeps aggregate scores from hiding actionable control-plane drift.

## Remediation sequence

1. Run the live diagnostic and raw source checks:
   - `python3 ~/.hermes/scripts/kanban_coverage.py --json`
   - `hermes kanban stats --json`
   - `hermes kanban assignees --json`
   - `hermes kanban dispatch --dry-run --json`
2. If stale blocked projections point to canonical brain notes that are already `done`, close only the stale Kanban projection with explicit `projection_only_no_task_execution` metadata. Do not claim new work or fabricate proof.
3. For active brain notes missing provenance:
   - If a real Kanban card/workspace exists, write back `kanban_task_id`, `kanban_workspace_path`, and projection status.
   - If no matching card exists, add an explicit `kanban_projection_exempt` / `agent_coverage_exempt` marker with a reason.
   - Never create fake cards or fake proof solely to increase coverage.
4. For remaining projection drift, read both the canonical brain note and Kanban DB/run history before mutating state:
   - `hermes kanban show <id>` plus `task_runs.summary` can reveal an explicit `review-required` / `needs eyes` worker outcome.
   - A Kanban `blocked` card with a real review-required run outcome can align with a brain note in `review`; classify it as a governed review gate (for example `blocked_review_gate_aligned`), not stale drift.
   - Do not force `blocked -> done` or edit brain lifecycle just to reach 100%; update the classifier only when the source/run evidence proves the projection is semantically aligned.
5. Re-run v2 coverage and ensure caps are empty or consciously explained.
6. Wire dashboard/V-state consumers to use the v2 score, while preserving legacy fields for compatibility.
7. Add regression tests for false-green prevention, stale projection caps, provenance/exemption counting, review-required blocked alignment, and v-state consumption.

## Agent architecture classification completion

When the user asks for “agent 分类” or asks to drive classification to 100%, check metadata separately from coverage:

- Scan active brain task notes (`pending`, `ready`, `claimed`, `running`, `review`, `blocked`, `retry`) for canonical classification fields: `lane`, `layer`, `project`, `architecture_target`, `completion_gate`, `iceberg_tier`, `iceberg_scope`, and `iceberg_confidence`.
- Treat `iceberg_tier` for Hermes self-architecture tasks as a system/control-plane tier, not only product UI tiers. `L` is appropriate when the task touches service/runtime/control-plane architecture rather than display-only UI.
- If Kanban says a card is blocked but the brain note still says running, inspect `hermes kanban show <id>` and `task_runs.summary`. A real `review-required` worker outcome should normally align the brain note to `review` with a lifecycle/projection audit line, not `done`.
- A classification 100% result requires zero missing canonical fields on active notes, empty `projection_drift`, empty caps, and tests/selfcheck after metadata changes.
- Scope: Hermes self-architecture agent/domain audits only. Applicability: when comparing Hermes runtime profiles and architecture domains to Google-style agent structure. Use a scoped, machine-readable Agent Card SSOT plus a validator and default-shadow runtime helper. Required card fields are goal, role, observation, memory, planning, tools, actions, policy, evaluation, collaboration, and escalation. Anti-condition: do not treat the card layer as broad runtime authorization; default-on specialist routing, always-on worker-prompt card injection, default-on conductor routing, canonical skill writers, or external side-effect executors still require explicit rollout evidence and separate verification. The safe scaffold pattern is: recommendation-only by default, `shadow` routing trace, and `apply` only under an explicit operator/env gate after profile-auth readiness is checked.
- For the safe progression from documentation SSOT → Agent Cards → read-only validator → default-off runtime scaffold → overall boundary, see `references/google-agent-card-runtime-scaffold.md`.

## Completion standard

A coverage target such as 90+ or 100% is satisfied only if:

- `agent_coverage_v2.score` reaches the requested target.
- No score caps are active, unless the user explicitly accepts a degraded result.
- Stale projections are zero or explicitly enumerated as non-blocking.
- `projection_drift` is empty for a 100% target; if an apparent drift is actually a governed review gate, prove it from Kanban run history and add a regression test before counting it aligned.
- Provenance improvement uses real refs or explicit exemptions, not fabricated proof.
- Tests and taskpool selfcheck are run and reported.

## Pitfalls

- Do not treat `ready=0` as healthy by default.
- Do not close brain tasks as `done` to improve coverage unless feature/task-specific evidence already proves completion.
- Do not mutate external adapters or task lifecycle beyond the projection-only scope without separate authorization.
- Do not hide remaining drift: list `projection_drift` task ids and reasons even when the aggregate score is above target.
