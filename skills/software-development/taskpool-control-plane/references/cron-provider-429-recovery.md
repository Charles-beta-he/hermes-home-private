# Cron Scheduler Recovery for Provider 429 Blocking

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Cron Scheduler Recovery — Model Provider 429 Blocking

When the Hermes cron scheduler appears stuck (jobs have `Next run` in the past but never fire), load `references/cron-scheduler-429-recovery.md`: it covers the diagnosis pattern (check `gateway.error.log` for repeated 429/RateLimitError on the default provider), the mechanism (all agent-based cron jobs share the default model, so 429 blocks the entire scheduler tick), and the recovery pattern (use `delegate_task` to manually execute the stuck job with `browser,file,terminal` toolsets, bypassing the blocked scheduler tick).

When daily/external-repo sidecars propose multimodel fields, treat the sidecar as advisory only. `daily_report_task_ingest.py` must normalize candidates locally: ordinary `work`/product/Lark tasks lose weak multimodel fields and do not trigger expensive panels, including retry/architecture-target heuristics; explicit `requires_multimodel: true` remains a strong override. P0/P1/P2 `evolution`/Hermes control-plane/self-strengthening/repo-intake candidates may keep the contract, must include `claude-code` in expected participants, and must resolve local evidence bundles or emit a TG/manual evidence request instead of blocking workers.

Reference: `references/self-proving-executor-proof-pattern.md` captures the AutoResearch-style self-proving executor pattern for Hermes/taskpool evolution: bounded command bundles, structured PASS/FAIL proof artifacts, nonzero failure exits, opt-in checkpoint side effects, and required control-plane verification before lifecycle advancement.

Reference: `references/mission-control-tower-dashboard.md` captures the Mission-in-Control-Tower dashboard pattern: expose MissionStore board/inbox as read-only plugin projections, use dashboard auth-aware fetch for `/api/plugins/...`, register imperative plugins to avoid host warnings, and keep the dashboard an operator cockpit rather than a second fact source.

Reference: `references/mission-bounded-continuation-and-flow-backlog.md` — Scope: long-running Mission control-plane recovery where the canonical Mission ledger shows exhausted tick budget, stale flow signals, explicit continuation decisions, or event-hook recursion from unintended multimodel spawning. Applicability: close current diffs first, answer only explicit decision packets inside the established local/reversible boundary, dispatch through the governed mission runner, keep local tick authority bounded (default user authorization interval is 60 ticks unless a narrower packet says otherwise), use `recover-signals` dry-run/apply with before/after evidence for stale backlogs, add fail-closed mission-envelope schema gates before autonomous stage work, and use `HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1` for bounded local maintenance runs that must not spawn multimodel workers. Anti-condition: do not use this pattern to authorize push/deploy/secrets/deletion/external delivery/production writes, active skill-store mutation, or cron/global env changes without a separate human gate.

Reference: `references/control-console-target-surface-calibration.md` captures the target-surface calibration rule for Hermes console/control-dashboard work: before edits or commits, distinguish standalone console apps from the Hermes Agent internal dashboard and verify the exact repository path.

Reference: `references/taskpool-to-mission-flow-bridge.md` captures the local-ledger bridge pattern for taskpool mutations waking a long-running objective/Mission controller: append scoped taskpool-status events, enqueue durable flow signals, schedule the existing runner, stay fail-soft, and avoid inline agent execution or external side effects.

Reference: `references/mission-event-runner-loop-closure.md` captures the follow-through pattern when a Mission bridge is only scheduling/showing work: add/use an explicit `dispatch-events --run-due` path that triggers the installed cron job and synchronously invokes the governed cron scheduler once, verify cron output and Mission ledger read-back, and keep `stage_report` as evidence-only so cron agents do not self-trigger indefinitely.

When the user asks for an engineering review, “多模型思考”, or a concrete plan to solve Hermes/taskpool long-term debt, use `references/taskpool-long-term-debt-strategy.md`: start with a read-only baseline, distinguish live runtime blockers from historical envelope/proof/continuation/handoff debt, add a debt ledger first, harden legacy envelope proof parsing/wall budgets, run the affected cron once to prove scheduler state, compact continuation/handoff artifacts via dry-run manifests, migrate proof debt only from existing evidence, and adjust `v_state` scoring only after observability exists.

When the user asks whether Hermes “工具调用逻辑” / tool-call execution may regress into non-convergence after a self-heal or health pass, use `references/tool-loop-convergence-audit.md`: audit the main conversation loop, tool executor, taskpool worker model chain, cron state, and live worker PIDs; separate current blockers from residual architectural risks such as missing batch-level wall-clock timeout, no-output provider timeout classification, and cron config/runtime churn.

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
