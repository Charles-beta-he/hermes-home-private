# Loop Engineering → Hermes taskpool control-plane mainline (2026-06-10)

Source intake: `/Users/charles/.hermes/docs/private/loop-engineering-wechat-intake-20260609.md`
Task: `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-09-吸收-loop-engineering-到-hermes-事件治理任务池循环.md`

## Objective

把 InfoQ/WeChat 的 Loop Engineering 热点，收敛为 Hermes 已有控制面的真实边界对照：哪些已经存在，哪些仍缺，下一步如何以低风险、可验证、可复跑的方式继续推进。

## Current-state reconcile

Already present in Hermes today:

1. Event-governed outer runner
   - `taskpool_dynamic_runner.py` 以 `brain_task_dispatch_tick.py --summary --no-state` 为观察入口。
   - 只有在明确 autorun 条件满足时才插入 `--autorun-step` 或 `--parallel-autorun`，不是 cron-only 盲跑。

2. Preclaim stop / human handoff gate
   - `human_escape_status()` 在 dynamic runner 外层先执行。
   - 当 human escape 触发时，runner 保持 summary/no-state 观察模式，并记录 `autorun_skipped_reason = human_escape_active_preclaim`。

3. Feedback gates instead of self-confirmation
   - `brain_task_multimodel_loop_runner.py` 内建 deterministic gates：`py_compile`、taskpool `selfcheck`、`proof-check`、`boundary-check`、`parallel-dispatch-dry-run`、`idle_runner`。
   - ratification 未通过时 fail-closed，而不是把“继续讨论”误当成 done。

4. Cost / quota observability
   - multi-model loop runner 已记录 `collect_model_quota_probe()`，把 intended quorum model 的本地 quota 可观测性写进证据包。

5. Non-mutating denial tests
   - `test_brain_task_dispatch_tick.py` 已验证 denied autorun 仍为 non-mutating。
   - `test_taskpool_dynamic_runner.py` 已验证 human escape 激活时不会偷偷加入 `--autorun-step` / `--parallel-autorun`。

## Architecture boundary

What this task should claim now:
- Hermes 已经具备 Loop Engineering 的核心“受治理循环”骨架：event-governed outer loop、feedback gate、budget/quota observability、stop/handoff、fail-closed ratification。

What this task should NOT claim now:
- 不应声称已经做成“live autonomous coding loops productization complete”。
- 不应把 article hype 当官方产品规格。
- 不应声称 runtime economics 已被完全证明；当前只证明 guardrail 已存在，且默认不会静默升级成 ambient expensive autorun。

## Chosen bounded landing step

本次选择的下一步不是继续放大 runtime 变更，而是先补一个可复跑 deterministic audit：

- Artifact: `/Users/charles/.hermes/scripts/loop_engineering_control_plane_selfcheck.py`
- Purpose: 把“Loop Engineering 已被 Hermes 控制面部分吸收”的论断，收敛成一个固定 JSON 自检，而不是散落在 task note / test 名称 / 口头总结里。
- Why this step first:
  1. 风险低：只读审计，不改 dispatch/runtime 行为。
  2. 可验证：直接输出 PASS/FAIL 和命中文件/行。
  3. 可复用：后续若继续加 loop budget、rollback、handoff contract，可把同一脚本扩展为正式 gate。

## Ordered mainline follow-ups

1. Land deterministic audit (this task).
2. Promote the audit into a broader reliability-harness/taskpool selfcheck surface.
3. Only then consider runtime deltas such as explicit iteration-budget / non-convergence / rollback state export for dynamic runner.
4. If runtime deltas are proposed, require targeted tests plus proof that default summary mode still does not silently enable expensive live autorun.

## Verification plan

- `python3 ~/.hermes/scripts/loop_engineering_control_plane_selfcheck.py --json`
- `python3 -m py_compile ~/.hermes/scripts/loop_engineering_control_plane_selfcheck.py`

## Evidence boundary

This note is an architecture reconcile + bounded-step landing note. It is not itself certification of a new runtime behavior change.
