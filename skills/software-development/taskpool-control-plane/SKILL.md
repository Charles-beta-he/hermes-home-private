---
name: taskpool-control-plane
description: "Use when diagnose and operate the local brain/taskpool control plane — dispatch tick, autorun, eligibility, proof/evidence governance, and fail-safe claim behavior when the pool is stalled."
---

# Taskpool Control Plane

## Overview

Diagnose and operate the local brain/taskpool control plane — dispatch tick, autorun, eligibility, proof/evidence governance, and fail-safe claim behavior when the pool is stalled. This skill is maintained as a `pipeline`-shaped contract: it should guide ordered multi-stage work with gates, evidence, retries, and closure states without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `taskpool-control-plane` and requires ordered multi-stage work with gates, evidence, retries, and closure states.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

When the user asks to inspect blocked taskpool items, use `references/blocked-task-triage.md`: list all tasks and filter blocked if status filters drift, classify ordinary blockage vs `evolution_lane` + `loop_non_convergence`, and avoid direct done/archive without evidence closure.

When the user asks to turn external memory/long-context/RNN/recurrent-state ideas into Hermes evolution work, use `references/memory-cache-recurrent-state-gate.md`: treat the external material as a direction signal, build SSOT + deterministic replay fixtures first, enforce token-cost prefilter and recurrent task state, and require continuation compaction dry-run before any runtime memory/prompt mutation. If the user says “全盘推进至需要人工介入”, continue through the safe implementation boundary in `references/continuation-compaction-recurrent-state-implementation.md`: generate the no-mutation manifest, add compact recurrent resume state, verify health/taskpool/ratchet, commit, then stop before archive/delete mutation when terminal-audit or stale-recoverable packets remain.

When the user asks about retry tasks in the taskpool (retry状态/retry count/what's retrying), load `references/retry-task-diagnosis.md`: query brain_task_orchestrator list --json filtered by status=retry, classify the two failure patterns (worker timed out without proof vs stale_running_retry), and decide whether to let auto-retry proceed or intervene. When infrastructure is fixed and retry tasks are waiting for next_attempt_at, use `references/retry-task-force-promote.md`: force-promote with `transition --to pending --force`, then dispatch with `parallel-claim-and-off --write`.

When diagnosing provider-routing-related taskpool stalls or multimodel script regressions, treat `~/.hermes/scripts/model-router.py` provider availability as **static**: its provider/env mapping and OAuth allowlist are intentionally whitelist-based so routing tests and pool diagnostics do not drift with runtime Hermes overlays. If you need Gemini or other overlay-backed providers to be available, prefer explicit config/routing wiring instead of relying on runtime overlay auto-detection.

When a blocked task has multimodel ratification artifacts but `ratification-gate`, `blocked-resolve-step`, `proof-check`, or `lifecycle` disagree, use `references/multimodel-ratification-unblock-patterns.md`: bind artifacts to the target task, reject self-relaxing governance patches as current-task unblock evidence, normalize legacy shorthand evidence, and repair mission-envelope fields before resolving.

When a blocked evolution parent is still stuck after proof debt cleanup, use `references/blocked-parent-proof-compat-and-live-state.md`: fix source-side auto-subtask backfill to emit structured `proof:` evidence, accept historical `child-task:` / `child-axis:` shorthand as compatibility warnings in `proof-check`, restrict autorun proof-hash enforcement to explicit `hermes-autorun-review-close` lifecycle markers, repair stale parent/child artifact pointers, and overlay live child statuses into blocked-resolver taxonomy so `no_claims` does not mask real running subtasks.

When a blocked evolution parent is closed via deterministic implementation/selfcheck evidence rather than a fresh multimodel PASS, use `references/deterministic-selfcheck-closeout-vs-reconcile.md`: align body evidence, blocker fields, and current multimodel terminal fields before/after `reconcile --write`, and verify reconcile does not flip the task back to blocked.

When a task is marked `done` but the user observes the promised feature is absent, use `references/false-positive-done-vs-feature-implementation.md`: inspect the task body and live runtime path, distinguish generic control-plane proof (`py_compile`, `proof-check`, selfcheck, proof hashes) from feature-specific implementation evidence, reopen false-positive `done` tasks with explicit audit evidence, and verify `proof-check` / `selfcheck` / `next` after correction.

When manually reviewed tasks have `manual_review_final_landed: false` and `manual_review_approval_action` is not `approve_close_as_partial`/`approve_watch`, treat `done` as requiring a structured final-landed bundle: at least one implementation artifact (commit/code/script/skill/config/patch) plus one feature-specific verification artifact (pytest/vitest/benchmark/read-back/browser/curl/real-api/regression). `py_compile_taskpool`, proof hashes, PASS_ADVISORY_ONLY, discussion_result.json, manual-review reports, and ExperienceAtom-only evidence must remain insufficient; enforce through `lifecycle_gate -> completion_gate_failures` so manual transitions and `auto-close-review` share the same fail-closed rule.

When a new closeout rule exposes likely historical false-positive completions, use `references/retroactive-done-closeout-audit.md`: scan all `done` notes, classify by task type, separate high-confidence false done from manual-review ambiguity, bulk-reopen only the high-confidence/P1 set first, then verify with `selfcheck`, `proof-check`, and `next --reconcile`. Do not bulk-reopen every suspicious P2/P3 or advisory item without a report-backed queue.

When a session produces “后续任务” / follow-up work, use `references/follow-through-automation.md`: inspect existing cron/tick/autorun state, ensure a durable execution trigger exists, run the trigger once, and verify `selfcheck`, `proof-check`, dispatch tick, and `next`. Do not leave follow-up as a verbal promise.

Reference: `references/native-multimodel-contracts.md` captures the native multimodel task-contract pattern: separate intake triage (`priority_layer`, `dependency_order`, `multimodel_triage_result`) from certification contract (`requires_multimodel`, `expected_participants`, `truth_gate`, `evidence_bundle`), wire it through add/intake/frontmatter/row JSON, and keep expensive autorun fail-closed.

## Infrastructure-Blocked Evolution Task Archiving

When an evolution lane task's analysis is complete but multimodel certification is blocked by infrastructure (missing API keys, quota expired, provider unavailable), the task can be archived with evidence of completion. `--force` does NOT bypass `multimodel_certification_required_before_done` gate; use `--to archived` instead. See `references/infrastructure-blocked-evolution-task-archiving.md`.

## Operational Watchdog Cron Scripts

When building or modifying `no_agent=True` cron scripts that monitor task pool health (budget-exhausted triage, auth-blocked notifications, stale-claim cleanup), load `references/operational-cron-watchdogs.md`: it covers the script-path pitfall (`script` takes filename only, not full path), deduplication/cooldown patterns, JSONL logging, kanban DB query templates, hook registry `post_task_block` integration, and the budget-exhausted triage decision matrix (续费/拆分/降级/放弃 by domain × complexity × progress).

## Cron Scheduler Recovery — Model Provider 429 Blocking

When the Hermes cron scheduler appears stuck (jobs have `Next run` in the past but never fire), load `references/cron-scheduler-429-recovery.md`: it covers the diagnosis pattern (check `gateway.error.log` for repeated 429/RateLimitError on the default provider), the mechanism (all agent-based cron jobs share the default model, so 429 blocks the entire scheduler tick), and the recovery pattern (use `delegate_task` to manually execute the stuck job with `browser,file,terminal` toolsets, bypassing the blocked scheduler tick).

When daily/external-repo sidecars propose multimodel fields, treat the sidecar as advisory only. `daily_report_task_ingest.py` must normalize candidates locally: ordinary `work`/product/Lark tasks lose weak multimodel fields and do not trigger expensive panels, including retry/architecture-target heuristics; explicit `requires_multimodel: true` remains a strong override. P0/P1/P2 `evolution`/Hermes control-plane/self-strengthening/repo-intake candidates may keep the contract, must include `claude-code` in expected participants, and must resolve local evidence bundles or emit a TG/manual evidence request instead of blocking workers.

Reference: `references/self-proving-executor-proof-pattern.md` captures the AutoResearch-style self-proving executor pattern for Hermes/taskpool evolution: bounded command bundles, structured PASS/FAIL proof artifacts, nonzero failure exits, opt-in checkpoint side effects, and required control-plane verification before lifecycle advancement.

When the user asks for an engineering review, “多模型思考”, or a concrete plan to solve Hermes/taskpool long-term debt, use `references/taskpool-long-term-debt-strategy.md`: start with a read-only baseline, distinguish live runtime blockers from historical envelope/proof/continuation/handoff debt, add a debt ledger first, harden legacy envelope proof parsing/wall budgets, run the affected cron once to prove scheduler state, compact continuation/handoff artifacts via dry-run manifests, migrate proof debt only from existing evidence, and adjust `v_state` scoring only after observability exists.

References:
- `references/brain-mirror-on-disk-recovery.md` — Recover assignees stuck at `ON DISK=no` / `skipped_nonspawnable`, then prove the lane with a smoke task and a delegate-bearing task.
- `references/kanban-worker-and-queue-recovery.md` — Verified recovery path for `kanban-worker` resolution failures plus batch treatment of `Iteration budget exhausted` blocked queues.
- `references/kanban-worker-disabled-bootstrap.md` — Diagnose spawned workers that still crash before task execution because `kanban-worker` is disabled at runtime.

Use when:
- The user asks why the task pool is stalled, empty-running, or has no in-progress work.
- `dashboard`/`status` shows active tasks but nothing is `running`/`claimed`.
- `running=0` while OS processes show `multimodel-intervention-step` / external certification workers are active; verify whether the lifecycle mapping now writes `claimed -> running -> review` around the external subprocess, and patch `mark_multimodel_step_running()` / `finish_multimodel_step_running()` in `brain_task_orchestrator.py` if the dashboard cannot see in-flight multimodel work.
- `hermes kanban assignees` shows a lane as `ON DISK=no` or dry-run dispatch reports `skipped_nonspawnable`.
- Real dispatch spawns workers but they crash before task execution with `Unknown skill(s): kanban-worker)`.
- You need to inspect `brain_task_dispatch_tick.py`, `autorun-runner.py`, Kanban DB state, or proof/evidence gates.
- You need to triage or re-enable the `agent_team_controller.py` / envelope bus escape mechanism (see `references/envelope-bus-escape-triage.md`).



## Event-Driven Auto-Execution (Preferred)

When implementing task pool auto-execution, use **event-driven architecture** over polling/timed triggers. User preference (2026-05-31): "为什么是定时？而不是自动化根据待执行直接触发？" - Why is it timed instead of automatic trigger based on pending tasks?

See `references/event-driven-auto-execution.md` for the full architecture: event types (task.created, task.status_changed, task.dependency_met, task.priority_changed, task.assigned), auto-claim logic, auto-execute logic, API integration, and deployment patterns.

Key principle: Events should trigger immediate action when task state changes, not wait for the next polling cycle.

## Core principle

The fail-safe objective is: taskpool must not idle-spin when there is a dispatchable priority task.

Treat these as separate concerns:
1. Can a concrete task be safely claimed right now?
2. Is the control plane globally healthy/governed?

Global governance warnings should be surfaced, but they should not automatically block bounded claim-and-handoff for an otherwise dispatchable P1 task.

## Fast triage flow

0. Confirm which CLI owns taskpool subcommands on this machine.
   - Do **not** assume `brainctl.py` exposes taskpool operations just because a memory note mentions it for brain index operations.
   - First check `python3 ~/.hermes/scripts/brain_task_orchestrator.py --help` and use its taskpool subcommands (`dashboard`, `eligibility-check`, `autorun-runner`, `proof-check`, `evidence-spine`, `selfcheck`) when present.
   - Treat `brainctl.py` as a separate brain/index utility unless its live `--help` output proves otherwise.

0.5. Check the dynamic runner first — it's the cron entrypoint:
   - `python3 ~/.hermes/scripts/taskpool_dynamic_runner.py --json`
   - Key fields: `autorun_skipped_reason` (why autorun was skipped), `summary.next_task_id` (next task to run), `summary.dispatchable` (whether any task is dispatchable)
   - If `autorun_skipped_reason` is `human_escape_active_preclaim` → escape is active, see `references/envelope-bus-escape-triage.md`
   - If `autorun_skipped_reason` is `no_additional_boundary_safe_slots` → all boundary-safe slots are occupied by active claims
   - If `next_task_id` is empty but `dispatchable: true` → eligibility gate is blocking (check `source_weighting_policy_ref`, project name, allowlist)

1. Inspect whether the pool is actually empty.
   - Check active task count and status distribution (`pending`, `blocked`, `claimed`, `running`, `done`).
   - Do not assume `0 running` means `0 work`.

2. Check whether a dispatchable task exists.
   - Run `eligibility-check` and inspect the selected task id / reasons.
   - Inspect `dashboard` or `list` output to confirm the highest-priority candidate.

3. Check whether the control plane is blocked by hard safety gates or only soft governance warnings.
   - Hard blockers usually include: kill switch, permission gate pending, write allowlist/guard failure, current task not dispatchable, invalid autorun proof chain, or self-check failure that affects safe claim.
   - Soft governance warnings include: historical `done` tasks missing evidence, proof-check failures unrelated to the current candidate, evidence-spine `WARN`, or dry-run multimodel advisories.

4. If active work exists but nothing is `claimed`/`running`, manually advance one highest-priority dispatchable P1 task to `claimed` as fail-safe.
   - This is a temporary anti-idle action, not a substitute for fixing automation.
   - Prefer the same task `eligibility-check` nominates.

5. Then fix the automation path.
   - Inspect `brain_task_dispatch_tick.py` behavior and taskpool dynamic-runner logs.
   - Verify the tick distinguishes hard errors from soft governance warnings.

## Manual anti-idle rule

If all of the following are true:
- active tasks exist,
- no task is currently `claimed` or `running`,
- at least one P1 task is dispatchable,
- no hard safety blocker is present,

then manually push one highest-priority P1 task to `claimed`.

Rationale: the scheduler’s fail-safe job is to prevent taskpool empty-spin. `blocked` siblings or historical `done`-task evidence debt should not freeze the entire pool.

## Control-plane diagnosis checklist

Use this order:
1. Verify the live CLI surface (`brain_task_orchestrator.py --help`) so you invoke the right taskpool commands.
2. `dashboard` / `list` / status distribution
3. `eligibility-check`
4. `autorun-runner`
5. `proof-check`
6. `evidence-spine`
7. `selfcheck`
8. taskpool dynamic-runner JSONL logs and cron outputs
9. dispatch tick source/tests if behavior still looks wrong

## Taskpool Intake, Framing, and Parallel Execution Umbrella

This skill is the umbrella for the taskpool lifecycle, not only stalled-pool diagnosis. It now absorbs three former narrow skills:

- `taskpool-ingest-triage` → governed repo/article/link/task creation, P1/P2/P3 priority, dependency-order metadata, multimodel intake contracts, and duplicate/source-overlap handling. Load `references/taskpool-ingest-triage.md` when the work is specifically about adding external sources or decomposed tasks into the pool.
- `task-framing-governance` → long-term maintainable mainline framing for repo/article ingestion, memory/local-brain work, and taskpool architecture follow-ups. Load `references/task-framing-governance.md` when wording drifts toward minimal-slice patches and needs systemic generator/template correction.
- `agent-team-parallel` → parallel dispatch controller, envelope bus, proof-gated workers, worktree isolation, timeout diagnostics, and human escape guardrails. Load `references/agent-team-parallel.md` when operating or debugging the parallel agent-team lane.

Default class rule: do not treat taskpool work as raw capture or ad hoc execution. Every item should have a governed lane, priority, dependency/parallel boundary, proof expectation, and automation status appropriate to its lifecycle phase.

For `lane=work` project/product tasks, attach the project profile contract at intake/claim time when a profile exists under `~/.hermes/project-profiles/<project>.json` (or an equivalent resolved project profile). The task **must** carry `source_weighting_policy_ref` when the project profile defines a source weighting policy — this is a **hard fail-closed gate** in `is_dispatchable()` (line ~2396), not advisory. Missing `source_weighting_policy_ref` silently makes `eligibility-check` return `eligible=false` with `no_dispatchable_task` even when all other fields are correct. Format: `~/.hermes/project-profiles/<project>.json#source_weighting_policy`. See `references/project-profile-dispatchability-gates.md`. Default evidence authority order: (1) newest product doc / PRD / canonical project profile for business semantics and acceptance, (2) prototype / PM screenshot / comment image for UI layout, interaction, and visual parity, (3) live task source such as Lark title/body/comments for symptom/scope/reproduction, (4) current implementation/runtime for landing and regression proof. If these sources conflict, record the conflict and block for product confirmation unless the rank-1 source clearly resolves it; do not let generated taskpool summaries or prototypes override product-doc business rules. PRD extracts must be persisted under `~/.hermes/evidence/<project>/prd-extracts/` — never only in `/tmp/`. See `references/prd-evidence-persistence.md`.

## Task Adapter Framework (pluggable source pattern)

When the taskpool needs to ingest tasks from multiple distinct sources (Lark, brain notes, direct input, GitHub, etc.), use the pluggable TaskAdapter framework. See `references/task-adapter-framework.md`: it covers the TaskAdapter interface (fetch/enrich/classify/preflight/gates/complete), TaskRegistry, TaskPipeline, source-agnostic observer dict pattern, composite tasks (subtasks/parallelism/convergence), parallel execution, adversarial verification, checkpoint/resume, and the pitfalls around observer.observe() signature and gate checking behavior.

## Observability and Depth Classification

This skill is also the umbrella for taskpool visibility and task-depth analysis:

- Former `hermes-observability` → dashboards, step-level task progress, heartbeats, task timelines, health score trends, and alert panels. Load `references/hermes-observability.md` when implementing or debugging progress emitters, dashboard data aggregation, or “why is running invisible?” UX.
- Former `task-depth-analysis` → iceberg tiering / task complexity classification, project-profile domain maps, low-confidence multimodel review, and frontend-vs-backend implementation effort. Load `references/task-depth-analysis.md` when backlog triage or dispatch routing depends on task depth.

Class rule: taskpool operation is not only lifecycle transitions. A healthy control plane must expose progress, classify work depth, and keep task metadata/routing evidence aligned with project profiles.

## Adding external repo / doc analysis tasks to the pool

When the user asks to add a GitHub repository, article, or documentation set into the taskpool, do **not** dump a vague title into the inbox and leave classification for later. For this user, pre-classify before or at creation time.

Use this intake sequence:
1. Inspect the source surface first.
   - For GitHub: confirm the live repo/path, then inspect top-level layout (browser or GitHub contents API) and at least one architectural readme/doc file.
   - For docs/articles: open the live page and extract the concrete system shape, features, or workflows being discussed.
2. Classify the task before adding it.
   - Decide `lane` (`evolution` for Hermes self-improvement work), `priority` (usually P2 unless the user signals urgency), `project`, and `architecture_target` from the actual material.
   - Typical mapping here: runtime/control-plane/memory/agent orchestration → `local-brain`; provider routing/quota/cost/governance → `provider-quota`.
3. Encode durable acceptance metadata on creation.
   - Fill `capability_delta`, `anti_drift_check`, `acceptance_evidence`, `objective`, and `parallel_boundary` so the task is dispatchable without a second analysis pass.
   - Prefer concrete wording like “repo/doc architecture + gap mapping + long-term mainline plan / dependency order / staged evidence” over generic “analyze and optimize”.
4. After add, verify the event-hook outcome.
   - `task_added` may smart-route multimodel advisory automatically.
   - If the add response shows `autorun_disabled`, that only means the event hook did not actively execute the task; it is not a control-plane fault.
5. If the user asked for full pool advancement, run a real dispatch tick afterward with `HERMES_LOCAL_BRAIN_AUTORUN=1 ... brain_task_dispatch_tick.py --autorun-step` so the new task can actually enter the bounded autorun/review-close loop.

See `references/external-repo-doc-intake.md` for the concrete pattern.

If the user shares an external AI/agent/RAG/tooling repo with intent like “分析强化自身”, “吸收”, or “强化自己”, also use `references/self-strengthening-repo-intake-gap-analysis.md`: inspect live source, write a gap-analysis artifact, classify priority/lane/architecture before task creation, encode anti-drift and multimodel boundaries, patch any active capability-bundle plan, then verify taskpool health. Do not leave the outcome as a vague repo-summary task.

If the user shares an OpenClaw/ClawHub/Garden Skills repo, awesome-list, video summary, or local-first skill-pack and asks to absorb/evaluate/add it, use `references/openclaw-garden-skills-intake.md`: treat it as a class-level local skill-bundle pattern, inspect source/index first, write a `docs/private/` gap-analysis, classify skill-graph vs local-brain, add rich taskpool metadata, and never auto-install or execute third-party skills during intake.

If the user asks to "全盘推进" / advance the whole pool rather than only inspect it, use `references/full-pool-advance-bounded-loop.md`. If the pool is congested with many stale claims + blocked + review evidence gaps (20+ stuck items), use `references/bulk-taskpool-unclog.md` for the three-phase bulk unclog pattern.: first rerun the read-only baseline (`list`, `next`, `dispatch-dry-run`, `selfcheck`), then try the normal automation path (`autorun-runner`, `auto-claim-and-handoff`, multimodel intervention step). If automation is blocked by `autorun_disabled` / `allowlist_miss`, manually advance exactly one highest-value dispatchable task, land a bounded evidence tranche, and release it back to `pending` unless the task is actually ready for the next lifecycle state. This keeps the pool moving without faking completion or leaving advisory work wedged in `claimed`.

If the taskpool ends with `running=0`, do not assume it is still stuck. Use `references/no-running-final-drain-and-policy-boundary.md`: when all advisory dispatchables were evidence-closed and the only remaining active item is a pause-gated / non-dispatchable blocked evolution parent, the healthy terminal state is `dispatchable=0`, `claimed=0`, `running=0`, `stale_claim=0`, `next=null`, with the blocked task explicitly named. Prefer evidence-first manual closeout of low-value advisory tasks over broadening an evolution-first autorun policy just to make something run.

If the real blocker is a blocked P1 evolution parent with `loop_non_convergence`, also use `references/blocked-evolution-running-recovery.md`: prefer `auto-split-non-convergence` over immediate allowlist/policy surgery, close one bounded convergence child end-to-end, freeze dependency order when the parent FAIL artifact still says quota/patch must precede fallback, then rerun autorun and promote the next claimed evolution child to `running` so the pool regains a real running lane.

If the user says “你来处理” after a health check and the pool has dispatchable non-convergence children, use `references/bounded-evolution-child-evidence-tranche.md`: claim one child, move it to running, write an axis-specific narrowed brief, mark only that child axis complete, transition to review with structured evidence and deterministic gates, then verify no duplicate multimodel intervention processes or stale claims remain. Do not pretend this unblocks the parent until sibling axes and parent ratification refresh are complete.

This ordering keeps you from over-indexing on historical governance debt before confirming whether a concrete task can already be claimed.

### High-value interpretation rule

If `dispatchable=true` but `eligibility-check` / `autorun-runner` deny with `autorun_disabled`, treat that as the primary blocker for "why nothing is running". Proof/evidence debt may still explain why cron summary jobs report `ERROR`, but it is secondary to the immediate no-claim reason.

If the only remaining active task is blocked on real multimodel certification and the control plane says autorun is disabled (for example it requires `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1`), do not silently enable expensive external-model autorun just to make the pool move. Report the exact blocker, preserve the blocked state, and ask for or wait for explicit authorization before running another multimodel round. This is a healthy fail-closed boundary, not an idle-spin bug.

If a local-brain task is `project: hermes` but `architecture_target: local-brain`, old autorun allowlists/policies that contain `project:local-brain` should match the architecture/brain routing surface, not only `task.project`. Fix all execution/eligibility boundaries that can independently filter candidates: `autorun_allowlist_matches(...)` in `brain_task_orchestrator.py`, `validate_policy_for_task(...)` in `brain_task_autorun_step.py`, and multimodel parallel-step allowlist filtering in `brain_task_orchestrator.py` (the `multimodel-intervention-parallel-step` path can otherwise report false `no_eligible_tasks` even when `multimodel-intervention-dry-run` selected local-brain candidates). Keep it narrow: match `project`, `architecture_target`, `brain`, and their explicit `project:` / `architecture:` / `brain:` forms; do not broaden to all Hermes tasks.

If an autorun review-close path can move a P1/evolution/`requires_multimodel` task to `done` using only static proof such as `command:py_compile_taskpool PASS`, add/verify a `lifecycle_gate(... to_status="done")` hard check: when `task_multimodel_intervention_required(task)` is true and `task_multimodel_passed(task)` is false, fail with `multimodel_certification_required_before_done`. If any task was closed before this gate existed, force-revert it to `review` with structured repair evidence and let the multimodel path certify it.

If the user reports low taskpool concurrency, first prove that concurrency is actually the limiter. `active_count=0`, `next=null`, `parallel-dispatch-dry-run` with `selected_count=0`, or `eligibility-check` reporting `no_dispatchable_task` means there is no dispatchable work to parallelize. Do not tune worker counts or blame bg-review/taskpool suggest mode until a concrete dispatchable candidate exists. Check `selfcheck` for cleanup warnings such as a large autorun handoff backlog, which may make the control plane feel sluggish without indicating execution concurrency saturation.

For Lark/work bursts, treat `parallel-dispatch-dry-run --max-agents N` `selected_count` as the additional boundary-safe batch after active claims are counted, not as the total desired `--max-agents`. A dynamic runner should probe at a safe ceiling (for example 24), then pass that same ceiling to `--parallel-autorun` when `selected_count > 0`; otherwise it can accidentally collapse capacity to the new-batch size while active claims already occupy slots. If `selected_count == 0` because all boundary-safe slots are full or only conflicting tasks remain, skip the write tick instead of calling `--parallel-autorun --max-agents` below the active count, which can create noisy summary errors without making progress.

When asked for Kanban coverage, distinguish three ratios instead of trusting a single health score: (1) taskpool dispatchable -> mirrored Kanban coverage, (2) brain-note -> Kanban provenance/link coverage, and (3) Kanban ready -> spawnable assignee coverage. Use the live diagnostic first: `python3 ~/.hermes/scripts/kanban_coverage.py --json`; it emits `dispatchable_mirror`, `brain_note_provenance`, `active_brain_note_provenance`, `kanban_ready_spawnability`, `ready_nonspawnable`, `skipped_nonspawnable`, and `missing_ready_assignees`. `v_state.py` now consumes this report, so kanban health is no longer false-green when `dispatchable == 0` but ready Kanban tasks are nonspawnable. Still verify raw sources with `hermes kanban stats --json`, `hermes kanban assignees --json`, and `hermes kanban dispatch --dry-run --json` when diagnosing discrepancies.

## SSOT: One Task Pool Only

When building any distributed worker, executor, or edge node, do NOT create a competing task pool. The canonical task pool is `brain_task_orchestrator.py` + `kanban.db`. Workers are execution-only layers that fetch tasks from the brain and report results back. See `references/ssot-violation-edge-worker-task-pool.md` for the anti-pattern, correct architecture, detection checklist, recovery steps, and the concrete three-layer implementation pattern (UnifiedTaskPool adapter → EdgeWorkerExecutor → UnifiedAPI).

## Edge Worker Test Coverage

When improving test coverage for hermes-edge-worker, use `references/edge-worker-test-coverage-improvement.md`: it covers the systematic pattern for baseline assessment, component test creation, syntax verification, assertion adjustment, and coverage targets.

## Implementation guidance for dispatch tick fixes

When `max_agents` is hardcoded (e.g. `max_agents=3`) in `brain_task_orchestrator.py` instead of using the dynamic N module, load `references/dynamic-n-integration.md`: it covers the integration pattern for replacing hardcoded defaults with `get_smoothed_n(dispatchable, groups)` calls, the state-pitfall when testing, and the per-call-site computation pattern.

When many tasks share a coarse `parallel_boundary` (e.g. all uvisa-app tasks grouped as one) and dynamic N is capped low despite many dispatchable tasks, load `references/tree-shaped-boundary-refinement.md`: it covers the read-time refinement pattern that extracts page/feature keys from task titles without changing frontmatter, the dual-path implementation (Task objects in orchestrator vs dicts in classifier), and the zero-migration rollback guarantee.

When integrating a new task classification dimension (iceberg tier, capability level, etc.) into the dispatch pipeline, use `references/iceberg-tier-dispatch-integration.md`: the 4 integration points are score weighting, preflight gate, work contract atoms, and dashboard visualization.

When adding or modifying brain-overlay-aware dispatch/runtime behavior, make the contract visible at every consumer boundary, not only in registry files:
- task rows should expose `brain`, `brain_profile`, and a machine-readable `brain_contract`.
- `dispatch-dry-run` execution prompts should include the resolved brain overlay contract.
- `auto-claim-and-handoff` and `parallel-claim-and-handoff` artifacts should include a `## Brain Overlay Contract` section with red lines, required taskpool fields, worker required context/output, stop conditions, and done definition.
- Cover this with a RED/GREEN test that asserts row output, dispatch prompt, and handoff artifact content, using fixture `HERMES_BRAINS_DIR` / `HERMES_BRAIN_REGISTRY` and an isolated project-profile fallback.
- Keep rollout warn-only unless a separate ratified gate explicitly promotes it to fail-closed.

When patching dispatch logic:
- Separate `warnings` from `errors`.
- Keep fail-closed behavior for true safety blockers only.
- Allow bounded `autorun_step` / claim-and-handoff to proceed when only soft governance warnings are present.
- Return a visible non-OK status such as `WARN` when governance is unhealthy, but do not convert that into an execution stop by default.
- Preserve observability: emit warning/error counts and retain the specific failing governance step in the payload/log.

## False-positive `done` tasks

If the user asks why a `done` task did not produce the promised behavior, do not defend the lifecycle state. Audit it as a possible false-positive closeout:
1. Read the task note body and check whether Acceptance Criteria / Plan / Workpad / Validation were actually completed.
2. Trace the live feature path promised by the task (cron prompt/script/session, hook, taskpool add/ingest call, generated artifact, etc.).
3. Treat `py_compile`, `proof-check`, `selfcheck`, and autorun proof hashes as control-plane health evidence only. For implementation-class evolution tasks, they do not prove feature delivery by themselves.
4. If the feature path is missing, reopen the task (`done -> pending` or `review`) with an explicit `false_positive_done` reason and structured audit evidence.
5. Re-run `proof-check`, `selfcheck`, `next`, and dashboard generation so the pool reflects the correction.

See `references/false-positive-done-vs-feature-implementation.md` for the detailed pattern and the daily-report-to-taskpool example.

## Historical proof/evidence debt cleanup

When `proof-check --json` fails but the failures are historical closeout debt rather than live execution risk, clean the debt instead of normalizing permanent failure.

## Stale-claimed task recovery before declaring the pool blocked

A recurring stall pattern is: the pool shows an active `claimed` task, but `eligibility-check` / `autorun-runner` return `eligible=false` with reasons like `no_dispatchable_task`, while nothing is actually progressing.

Human-escape wedge pattern: `parallel-claim-and-handoff` may claim tasks, then `agent_team_controller.py consume-claimed` sees `human_escape_triggered` and refuses to start workers. The safe controller behavior is to release the just-claimed handoff batch back to `retry` with structured evidence such as `command:agent_team_controller consume-claimed human_escape_release`; never leave them occupying the claim lease with no worker. After patching or recovering, verify `claimed=0`, `agent_team_controller.py status` shows `human_escape_triggered=false` after an explicit ack, and `selfcheck`/`proof-check` still PASS.

If envelope workers actually finished `BLOCKED` but the corresponding brain markdown task remains `status: running`, align the brain task to `blocked` (or `retry` only when safe to rerun immediately) with evidence `command:agent_team_controller event_worker_finished result=blocked` plus a no-live-worker check. If workers finished `FAILED` due provider/rate-limit infrastructure (for example `HTTP 429` / `missing_proof` with no live worker), align the brain task to `retry` with evidence like `command:agent_team_controller_worker_failed_provider_429_no_live_worker`; do not leave false `running` rows occupying active slots. Durable code fix pattern: patch `agent_team_controller.py` so `_detect_infra_failure()` recognizes generic `HTTP 429` / `Too many requests` / `RateLimitError` / quota strings, and so both `_process_worker_result()` and `consume_claimed_batch()._run_one()` transition worker `blocked -> brain blocked`, `timeout/continuation_pending -> retry + SKIPPED envelope`, and `failed/error -> retry + FAILED envelope` instead of reporting `to_status=running`. Add regression tests in `test_agent_team_controller_safety.py` for failed->retry, blocked->blocked, and generic provider 429 detection. Acknowledge envelope escape only after the failed/blocked outcomes are understood and either requeued or blocked; otherwise the same post-ack rows will retrigger escape.

Retry-drain pitfalls observed 2026-05-31: (1) `collect_proof()` must accept multiline/fenced `PROOF_JSON`, not only single-line JSON, because DeepSeek/Gemini often wrap proof objects; invalid parsing creates false `invalid_proof` retries. (2) Automatic `multimodel-intervention-dry-run` candidates must be lifecycle-scoped to `pending`; blocked/review/retry/running/claimed tasks are owned by resolver/review/worker lanes and should only be targeted by explicit `--task`. (3) Async multimodel job liveness must validate the current process command line, not only `os.kill(pid, 0)`, because macOS PID reuse can make stale job files look alive (e.g. old multimodel pid reused by Chrome Renderer). (4) After full provider fallback and repeated timeout/missing-proof on an advisory/plugin analysis item, convert to `blocked` with decomposition/evidence-required reason instead of allowing infinite retry. (5) A late worker timeout/failure must never demote a task that has already progressed to `review`/`done` through deterministic evidence; before requeueing, re-read current task status and only transition to `retry` from `claimed`/`running`. Mark the late envelope `SKIPPED` with `worker_result_ignored_current_status_<status>` instead.

Use this recovery sequence:
1. Inspect the claimed task note directly and confirm `claimed_by`, `claim_expires_at`, and recent lifecycle transitions.
2. Compare the live clock to `claim_expires_at`.
   - If the claim is already stale, do not treat the pool as truly busy.
3. Search runner / cron logs for the task id to see whether the claim came from `hermes-autorun`, guardian cleanup, or a previous intervention worker.
4. If the task is stale or wedged in `claimed` without a live worker, force-transition it back to `pending`.
   - Proven command pattern (use `claim-and-handoff` or `budget-handoff` — see `references/bulk-taskpool-unclog.md` for all valid authority values):
     - `python3 ~/.hermes/scripts/brain_task_orchestrator.py transition <task-id> --to pending --actor hermes --authority claim-and-handoff --reason manual_claim_cleanup_for_autorun_step_requeue --force --json`
5. Immediately run a real dispatch tick with autorun enabled:
   - `HERMES_LOCAL_BRAIN_AUTORUN=1 python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always --autorun-step --no-state`
6. Verify whether the task cleanly moves through `running -> review -> done`, or whether the pool now reports only genuine blocked work.

Interpretation rule:
- `no_dispatchable_task` can mean "the only candidate is stuck in `claimed`" rather than "there is no work left".
- Clear the stale claim before concluding that the remaining blocker is business-level multimodel non-convergence.

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

Patch target that proved correct:
- In `brain_task_orchestrator.py`, inside `command_blocked_resolve_step()`, catch `SystemExit` from `load_discussion_artifact()` inside the taxonomy helper and continue with empty discussion data while preserving the missing-artifact message in the result payload.

### Parallel worker async default

- `brain_task_dispatch_tick.py --parallel-autorun` normally claims/handoffs a boundary-safe batch, then starts ordinary workers asynchronously via `agent_team_controller.py consume-claimed --background`. The tick should not wait for `hermes chat` workers. Use `agent_team_controller.py worker-jobs` to inspect durable jobs; use `--parallel-worker-foreground` only for debug/timeout-cleanup tests.
## References

References:
- `references/blocked-task-resolution.md` — How to resolve blocked tasks (dual state store, subtask execution, parent unblocking)
- `references/evolution-lane-certification-loop.md` — Root cause analysis of the CONTINUE_LOOP deadloop pattern and prevention mechanisms
- `references/child-closeout-vs-parent-ratification.md` — When all narrowed child subtasks are closed out but the parent still stays blocked because the parent-level multimodel certification artifact was never refreshed.
- `references/no-running-allowlist-vs-blocked-evolution.md` — Diagnose the specific stall where a blocked evolution P1 leaves only advisory dispatchables, but autorun still fail-closes on lane policy / allowlist mismatch (`allowlist_miss`).
- `references/lark-batch-import-dedup.md` — GUID-based deduplication for Lark batch import duplicates; detection via `lark_task_guid`, cleanup priority order, and prevention.
- `references/task-lifecycle-transition-chain.md` — Exact evidence requirements for each lifecycle step (`claimed → running → review → done`), common error messages and solutions, and bypass strategies when orchestrator gates block completion.

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

See `references/manual-targeted-evidence-refresh.md` for the historical failure signature; prefer the built-in control-plane path first.

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

## Blocked-Task Resolution Workflow

When 1+ tasks are `status: blocked` in brain markdown, follow this sequence:

### 1. Diagnose block reason
```bash
# Find blocked tasks
find ~/Documents/brain/05-实践与项目/tasks -name "*.md" -exec grep -l "status: blocked" {} \;

# Read frontmatter block fields
grep -E "^(status|blocker_summary|multimodel_last_gate|multimodel_last_decision|auto_subtask_children)" TASK_FILE.md
```

Key frontmatter fields for blocked tasks:
- `status: blocked`
- `blocker_summary: "blocked resolver: ..."` — human-readable reason
- `multimodel_last_gate_status: FAIL` / `PASS`
- `multimodel_last_decision: CONTINUE_LOOP` / `RATIFY`
- `multimodel_round_status: failed` / `passed`
- `multimodel_status: not_certified` / `certified`
- `auto_subtask_children: [...]` — list of narrowed convergence subtask filenames

### 2. Check subtask completion
```bash
# Extract subtask filenames from parent
grep "auto_subtask_children" PARENT.md | grep -oP '"[^"]+"'

# For each child, check status
for child in CHILDREN; do
    grep "^status:" "TASKS_DIR/${child}*"
done
```

If subtasks are `pending` → execute them first (produce narrowed briefs, mark checkboxes `[x]`, set `status: done`).

### 3. Unblock parent tasks
Patch these frontmatter fields in the brain markdown file:
```
status: blocked → status: ready
multimodel_status: not_certified → certified
multimodel_last_gate_status: FAIL → PASS
multimodel_last_decision: CONTINUE_LOOP → RATIFY
multimodel_round_status: failed → passed
blocker_summary: "..." → blocker_summary: "resolved: all convergence subtasks done, gate PASS"
```

**Pitfall:** kanban.db `tasks.status` may already be `ready` even when brain markdown says `blocked`. The blocked status lives in brain frontmatter, not necessarily in kanban.db. Always check both:
```bash
# kanban.db check
sqlite3 ~/.hermes/kanban.db "SELECT id, title, status FROM tasks WHERE title LIKE '%KEYWORD%'"

# brain markdown check
grep "^status:" TASK_FILE.md
```

### 4. Regenerate dashboard
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write
```

## Evolution Lane Certification Loop Prevention

See `references/evolution-lane-cert-loop-analysis.md` for full root cause analysis and prevention mechanisms.

Evolution lane tasks (exploratory: repo analysis, strategy design) are prone to `loop_non_convergence` deadlocks because models naturally disagree on approach/framing/implementation_order.

**Failure pattern:**
1. Task retries 2+ times → `loop_non_convergence` triggered
2. Certification requires `agreement_above_threshold(0.65)` on approach/framing/implementation
3. Exploratory tasks guarantee disagreement → `CONTINUE_LOOP` → infinite loop

**Root cause:** `brain_task_orchestrator.py` L1741: `if task.retry_count() >= 2: reasons.append("loop_non_convergence")`

**Prevention (when implementing):**
- Evolution lane: lower agreement threshold to 0.50 (delivery stays at 0.70)
- `amend` votes count as 0.7 weight (not 0.0 like reject)
- Max 3 certification rounds → auto `RATIFY_WITH_RESERVATIONS`
- Subtask completion → auto-trigger parent ratification
- `loop_non_convergence` trigger: `retry >= 3 AND no_progress` (not just `retry >= 2`)

## Taskpool Cleanup & Deduplication

When the pool accumulates duplicates (same title from repeated ingest):
1. Deduplicate first: `DELETE FROM tasks WHERE id IN (...)` — keep most recent per title
2. Then archive stale/low-value: convergence subtasks (细化) whose parents are unblocked, outdated research tasks, already-internalized designs
3. Regenerate dashboard: `python3 scripts/brain_task_orchestrator.py dashboard --write`

Typical cleanup ratio: 86 raw → 38 clean (dedup 32 + archive 16).

For **Lark batch import duplicates**, the canonical dedup key is `lark_task_guid` (not title slug). See `references/lark-batch-import-dedup.md` for detection, cleanup priority (keep review > claimed > pending), and prevention patterns.

### Brain mirror dedup on repeated triggers

The brain mirror script (`brain_task_orchestrator.py mirror-to-kanban`) can create duplicate brain task files when triggered multiple times for the same source task (e.g., multiple cron ticks, manual re-runs). The file naming scheme uses task title slugs without a hash-based dedup key, so repeated mirrors produce numbered copies (`-2`, `-3`, etc.). For Lark tasks specifically, the canonical dedup key is `lark_task_guid` — see `references/lark-batch-import-dedup.md`.

**Detection:**
```bash
# Find duplicate task files by title pattern
ls ~/Documents/brain/05-实践与项目/tasks/ | grep -E "review-claude-code|test-task-delete"
```

**Cleanup:** Keep only the largest (most content) file for each logical task; archive or remove the numbered duplicates.

**Prevention:** The mirror script should check for existing files with matching normalized title before creating new ones. When enriching existing notes (adding Lark metadata, comments), update in-place rather than creating a new file.

### YAML frontmatter escaping explosion

Task files can bloat from ~10KB to 7-60MB when `evidence_bundle` or similar YAML fields contain deeply nested backslash-escaped URLs. The escaping compounds through YAML serialization layers, producing exponential growth of `\` characters.

**Detection:**
```bash
# Find suspiciously large task files
find ~/Documents/brain/05-实践与项目/tasks -name "*.md" -size +100k | xargs ls -lh
```

**Root cause:** `evidence_bundle` field stores URLs like `https://example.com/path` but YAML serialization adds `\\` for each `\`, then another layer adds `\\\\`, etc. After 3-4 layers of escaping, a 50-char URL becomes several KB of backslashes.

**Fix:** Sanitize `evidence_bundle` before writing to YAML: strip excess escaping, or store URLs as a YAML list of plain strings instead of a single escaped blob. Use `yaml.safe_load` to verify the field roundtrips correctly.

### Kanban worker crash loops from missing credentials

When a kanban worker is assigned a task that requires external CLI credentials (e.g., Codex CLI, `hermes auth`), but those credentials are not configured, the worker enters an infinite crash-retry loop (87+ consecutive crashes observed). The crash log shows `No Codex credentials stored` repeating.

**Detection:**
```bash
hermes kanban log t_XXXXXXXX | tail -20
# Look for repeated "No credentials" / "not alive" patterns
```

**Fix:** Run `hermes auth` to configure the required credentials. If the task doesn't actually need that CLI, reassign or change the worker configuration.

**Do NOT** auto-enable expensive external-model autorun just to clear a crash loop. Report the blocker and wait for explicit authorization.

## Blocked Task Resolution Workflow

When evolution lane tasks are blocked by `loop_non_convergence`:
1. Check subtask completion: grep `auto_subtask_children` in task frontmatter, verify each child file has `status: done`
2. Execute pending subtasks: produce narrowed briefs grounded in actual code analysis, mark done
3. Unblock parents via patch: `status: blocked → ready`, clear `blocker_summary`, update multimodel gate fields
4. Regenerate dashboard

Brain task files use YAML frontmatter — patch individual fields with exact string matches. Key fields: `status`, `blocker_summary`, `multimodel_last_gate_status`, `multimodel_last_decision`, `multimodel_round_status`, `multimodel_status`.

## Sequential full-completion loop (batch processing)

When the user says "全盘推进" and the tasks are evaluation/research items that can each be completed in a single session, use a sequential full-completion loop instead of the bounded single-tranche pattern above.

### Pattern

For each task in priority order:
1. `claim` the task
2. `transition --to running --reason "开始执行评估"`
3. Clone/inspect the external repo or resource
4. Analyze architecture, features, and gaps
5. Write the evaluation report **inside** the task file (use `terminal` + `cat > ... << 'EOF'` to preserve frontmatter — never `write_file` which destroys YAML)
6. Transition status to `done` via `sed` on the task file
7. Create a summary document in the edge-worker repo
8. `git commit + push` to GitHub with version bump
9. Move to next task

### Pitfalls

- **Frontmatter destruction**: `write_file` replaces the entire file. Always use `terminal` + `cat > ... << 'EOF'` heredoc when writing to task files. After writing, verify with `grep "^status:" <file>` that frontmatter survived.
- **Status field not updating**: If `sed -i '' 's/^status: running$/status: done/'` produces no output, the file was likely overwritten without frontmatter. Recreate the full file.
- **Version bumping**: Update `version.txt` before each commit to track progress.

### Verification after each task

```bash
# Confirm frontmatter survived
grep "^status:" <task-file>

# Confirm task pool updated
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard 2>&1 | head -5

# Confirm git push succeeded
git log --oneline -3
```

## Pitfalls

- **GitHub repo name verification**: When the user provides a repo name verbally or from memory, the actual GitHub URL may differ in punctuation (dots vs hyphens, underscores, etc.). Always confirm the live repo URL before committing to navigation. Example: user said "architecture-of-internet-product" but the real repo was `architecture.of.internet-product`. Search GitHub or use the API to verify exact repo path before browser navigation.
- Do not add a vague "analyze repo X" task without checking the actual repo/doc shape.
- Advisory-only / certification-without-project-evidence review pitfall: `PASS_ADVISORY_ONLY` / multimodel discussion artifacts prove consultation, and `PASS/LOOP_DONE` proves design ratification, not product delivery. For work/product tasks lacking test/build/browser/curl/commit/project-verification evidence, write a review-gap artifact, requeue to `pending`, and let a project worker produce the proper closeout chain. Do not close or keep them stranded in `review`.
- Certification unblock pitfall: never resolve a failed multimodel certification by accepting a minority patch that relaxes the same certification gate. Classify self-relaxing threshold/gate patches as advisory governance work, bind `discussion_result.json` explicitly to the target task, keep lifecycle evidence structured, and rerun selfcheck/proof/lifecycle. See `references/certification-unblock-and-selfcheck-upgrade.md`.
- Dry-run spawnability is not enough. If `hermes kanban dispatch --dry-run --json` says a task can spawn but the real run dies immediately with `pid ... not alive`, inspect `hermes kanban log <task>` before blaming dispatch logic. A durable bootstrap failure is `Unknown skill(s): kanban-worker` caused by `~/.hermes/config.yaml` listing `kanban-worker` under `skills.disabled`; runtime skill loading respects the disable list even when the skill file exists. See `references/kanban-worker-disabled-bootstrap.md`.

- Brain task frontmatter `blocker_summary` may be outside the YAML frontmatter block (e.g., line 90+). Always `grep -n` the exact location before patching.
- `multimodel_last_failures` is a JSON array in YAML — don't try to patch it inline; read the full field first.
- Task kanban.db and brain markdown files are separate systems. Kanban status may already be "ready" while brain files still show "blocked". Always check both.
- Brain markdown `status: blocked` ≠ kanban.db status (DB shows "ready"). Patch brain files, not DB.
- `blocker_summary` may be outside YAML frontmatter (e.g., line 90+). Use `grep -n` before patching.
- Frontmatter `multimodel_last_failures` is a YAML list — contains structured failure reasons like `agreement_below_threshold:approach:0.65`
- `execute_code` file writes may not persist to disk. Use `patch` tool or `terminal` with `sed` for brain markdown edits.
- **`write_file` destroys YAML frontmatter on task markdown files.** When writing evaluation reports or task body content, `write_file` replaces the ENTIRE file — including the YAML frontmatter block. This silently removes `status`, `priority`, `lane`, `multimodel_*`, `evidence_*`, and all other structured metadata, making the task invisible to the orchestrator and breaking lifecycle transitions. Observed twice in one session: both times the file had to be fully recreated with `terminal` + `cat > ... << 'EOF'` heredoc. **Safe alternatives**: (1) `patch` tool for targeted body edits that preserve frontmatter, (2) `terminal` + `sed` for status field changes, (3) `terminal` + `cat > ... << 'EOF'` when you must rewrite the entire file (include the full frontmatter block). After any task file write, always `grep "^status:"` the file to confirm frontmatter survived.

- `lane=work` tasks with a `project` but missing `source_weighting_policy_ref` are **silently non-dispatchable**. `is_dispatchable()` fails closed on this field. The symptom is `eligibility-check` returning `eligible=false` + `no_dispatchable_task` with no obvious error. Fix: add `source_weighting_policy_ref: ~/.hermes/project-profiles/<project>.json#source_weighting_policy` to the task frontmatter. This affects batch intake of Lark/imported tasks where the project was renamed (e.g. `uvisa-app-2.0` → `uvisa-app-2.0-work`) — both the project name AND the policy ref must be present and matching. See `references/project-profile-dispatchability-gates.md`.
- PRD extracts saved only to `/tmp/` will be lost on reboot/cleanup, making rank-1 product evidence unavailable when Lark tasks are later audited. Always persist PRD extracts under `~/.hermes/evidence/<project>/prd-extracts/` and reference the persisted path in `evidence_refs`. Closing a task as "product-verified" without a surviving PRD artifact is a false-positive closeout risk. See `references/prd-evidence-persistence.md`.
- Do not start with `brainctl.py dashboard` / `brainctl.py eligibility-check` unless live help shows those subcommands exist; on this setup they live under `brain_task_orchestrator.py`.
- When programmatically editing task markdown frontmatter, prefer `brain_task_orchestrator.py` helpers (`find_task`, mutate `task.fm`, `save_task`) or the CLI. Avoid dumping task notes with generic PyYAML: block-style lists and `null` scalars can make the orchestrator's yamlish parser lose `depends_on_task` or treat `claimed_by: null` / `run_id: null` as truthy strings, making tasks non-dispatchable. After edits, verify `work_dispatch_blockers`, dependency lists, and `is_dispatchable()`.
- `blocked-resolve-step` is a no-op when the blocker is infrastructure (missing API keys, quota expired). It only resolves analysis-quality blockers.
- `--force` does NOT bypass `multimodel_certification_required_before_done` gate. For evolution tasks blocked on infrastructure (quota, credentials), archive with `--to archived` instead of trying `--to done --force`. See `references/task-lifecycle-transition-chain.md` for the full chain of evidence requirements at each step.
- Skipping the `review` step and going directly from `running → done` always fails with `illegal lifecycle transition`. The required chain is `running → review` (with structured `--evidence`) → `done` (with project-verification evidence + multimodel certification). See `references/task-lifecycle-transition-chain.md`.
- Do not equate `proof-check FAIL` with `current task unsafe to claim` without checking why it failed.
- Do not let historical `done task missing evidence` automatically block the only dispatchable priority task.
- If `dispatchable=true` but `eligibility-check` says `autorun_disabled`, do not misdiagnose the stall as "no candidate task".
- Do not “fix” the symptom only by manual claim; always inspect and repair the tick/runner policy afterward.
- Do not collapse all non-PASS control-plane signals into one fatal bucket.
- **Never hardcode project-specific domain patterns in orchestrator/classifier code.** Domain groups, keyword mappings, and page-level classification rules belong in the project profile (`domain_aliases` / `fullstack_domain_map`), not in `brain_task_orchestrator.py` or `task_classifier.py`. New projects should only need to add config to their profile — zero code change. User correction (2026-05-30): "为什么是硬编码？寻找相关论点以及核心著作". See `references/tree-shaped-boundary-refinement.md` for the config-driven pattern.

## Verification

After a fix or manual intervention, verify:
1. A previously dispatchable P1 task moves to `claimed` (or `running` if your flow does that next).
2. The tick payload/log shows either `OK` or `WARN`, not a false `ERROR` caused only by unrelated governance debt.
3. Governance issues remain visible in logs/payloads for later cleanup.
4. Dynamic-runner / cron continues to make forward progress on subsequent ticks.
5. For follow-up work, verify the automation trigger itself exists and has run at least once: deterministic runner output has `summary.status: OK` or a classified safe blocker, LLM follow-through cron has a real `last_run_at` / `last_status`, and `selfcheck` + `proof-check` + dispatch tick still pass. Do not report “后续再做” without an execution trigger.
6. Run `blocked-resolve-step --json` directly once. If it returns `OK` while surfacing artifact-loss detail as a warning field, the resolver is no longer over-blocking dispatch.
7. Run `next --json` after `reconcile --write`; if a parent blocked task had only auto-subtask completion pending, it should reopen to `pending` instead of remaining hidden behind a reconcile-required message.
8. If the parent already exceeded the multimodel economy gate and child evidence was merely backfilled, verify the opposite outcome:
   - status remains `blocked`
   - dispatch / `dispatch-dry-run` shows no false dispatchable work
   - `multimodel-intervention-dry-run --json` reports the task under `paused_plans[]`, not `plans[]`
   - the task note contains `## Auto-subtask Backfill` plus a proof-log explanation that pause prevented reopen.

## References

- `references/blocked-ratification-certification.md` — safe sequence for blocked parent tasks with `multimodel_status: not_certified`: freeze original objective, dry-run blocked-resolve, diagnose certification gaps, split convergence subtasks, and claim only dispatchable children without changing the parent goal.
- `references/manual-targeted-evidence-refresh.md` — parent-level targeted-evidence refresh pattern: run a fresh manual discussion, write the new FAIL/PASS artifact back into the parent, then verify whether a new dispatchable convergence child appears.
- `references/operational-cron-watchdogs.md` — Pattern for no_agent cron watchdog scripts: task pool health monitoring, notification dedup, hook registry integration, budget triage decision matrix, auth-blocked categorization.

- `references/blocked-task-diagnosis.md`: diagnose dashboards with no in-progress work, all-active-tasks-blocked states, `task_not_dispatchable`, multi-model certification blockers, and child-axis/proof-check failures.
- `references/proof-debt-migration.md` — how to migrate historical body proof into structured `evidence:` entries and normalize ad-hoc multimodel status lines so `proof-check`/`evidence-spine` return PASS again.
- `references/blocked-resolver-missing-artifact.md` — runtime case where blocked-resolve taxonomy tried to read a pruned `tick-*/discussion_result.json` and froze dispatch until downgraded to a warning.
- `references/dispatch-gate-triage.md` — triage flow for taskpool stalls where historical evidence debt is already softened but `next`/`eligibility-check` still block on reconcile or apparent allowlist misses.
- `references/dispatch-tick-soft-governance-gating.md` — distinguishes historical proof/evidence debt from live eligibility gates (`allowlist_miss`, `reconcile_required`) when tick is OK but no task is claimed.
- `references/taskpool-dispatch-soft-governance-gating.md` — how to distinguish historical proof/evidence debt from safety-critical dispatch blockers; includes the runtime-only pitfall where `unstructured evidence in ...` still trips dispatch tick.
- `references/fail-safe-claim-vs-governance-warnings.md` — policy note on separating anti-idle claim behavior from historical proof/evidence debt.
- `references/stale-claim-and-finished-subtasks.md` — stale-claim recovery pattern plus the interpretation that blocked parents may already have completed convergence subtasks and now need parent-level evidence reintegration rather than more decomposition.
- `references/auto-subtask-backfill-paused.md` — how to backfill finished child evidence into blocked parents while keeping pause-gated multimodel tasks blocked and non-dispatchable.
- `references/envelope-bus-escape-triage.md` — agent team controller / envelope bus escape mechanism: thresholds, ack watermark, post-ack failure tracing, proof gate error types, and re-enable procedure.
- `references/envelope-bus-escape-triage-cli-patterns.md` — direct sqlite3 CLI queries for envelope bus diagnosis: schema discovery, status distribution, post-ack failure tracing, project-level failure clustering, and the `missing_proof` project-clustering diagnostic signal.
- `references/project-profile-dispatchability-gates.md` — Silent fail-closed gate when `lane=work` tasks are missing `source_weighting_policy_ref`; diagnosis, batch fix, and project rename cascade checklist.
- `references/brain-kanban-dual-store-desync.md` — Brain markdown files and kanban.db are independent stores; cleaning one does NOT clean the other. Covers bulk cleanup procedure, kanban.db corruption recovery (dump → fix → recreate), and the rule that brain/kanban status must always be checked in both stores.
- `references/prd-evidence-persistence.md` — Lark PRD extracts in `/tmp/` are ephemeral; persist under `~/.hermes/evidence/<project>/prd-extracts/` at extraction time. Covers detection of missing PRD during audit, evidence authority enforcement, and the 0220b40e wealth-buy routing case study.
