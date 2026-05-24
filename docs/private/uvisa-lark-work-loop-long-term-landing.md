# UVISA/Lark work 任务池长期闭环一次落地方案

Generated: 2026-05-24
Multi-model packet: `/Users/charles/.hermes/tick-20260524-001835-520679-p30332-c6a39411-523b8444`
Live contract implementation: `/Users/charles/.hermes/scripts/uvisa_lark_work_contract.py`

## 1. 多模型共识

Claude / GPT-5.5 / DeepSeek / MiMo / Gemini 的结论一致指向：问题不是简单把 `agentTeam` 并发数调高，而是控制面闭环缺了任务级机器验收契约。

根因分层：

1. Verifier gap：已有通用 truth/evidence gate，但没有在每个 Lark 任务入池时生成 task-specific acceptance atoms + proof mapping，导致 08235149 这类数据正确性任务可能用泛化 UI 证据假关闭。
2. Branch/workspace gap：三个 UVISA 仓库没有统一任务循环分支；同仓并发写如果没有 worktree/merge queue，会把多个任务 diff 串在一起。
3. AgentTeam execution gap：`agent_team_controller.py` 当前 cycle 中直接同步调用 `delegate_to_worker`，cron tick 被 worker 执行吞掉；`raw_n=3` 不等于真并发。
4. State-machine gap：worker 仍可能让 envelope 到 DONE；长期正确形态应是 worker 只提交 artifacts，controller/proof gate 决定 PR、merge、online regression、Lark close、TG notify。

## 2. 最终架构

```
Lark assigned task
  -> intake/dedup/enrich
  -> uvisa_lark_work_contract.generate
       - task_type
       - repos
       - branch_namespace
       - acceptance_atoms
       - required proof types
  -> scheduler lease
       - conflict group
       - worktree workspace
       - write boundary
  -> worker execution
       - local tests/build
       - proposed proof bundle only
  -> controller proof gate
       - acceptance atom mapping
       - source-to-sink equality if data task
       - 1512x982 target-bound UI evidence if UI task
  -> PR open
  -> per-repo serial merge queue
  -> remote deploy/package monitor
  -> online browser regression
  -> Lark final closeout guard
  -> TG notification with evidence dir
  -> done
```

## 3. 状态机

`pending -> planned -> leased -> running -> worker_done_pending_proof -> proof_verified -> pr_opened -> merge_queued -> merged -> online_regression_verified -> lark_closed -> tg_notified -> done`

Fail-closed blockers：
- missing_acceptance_atoms
- missing_runtime_proofs
- missing_pr_url
- missing_merge_commit
- missing_online_regression_evidence
- missing_lark_close_response
- missing_tg_evidence_dir_notification

## 4. Acceptance atoms schema

Each Lark task receives a contract:

```json
{
  "schema": "uvisa_lark_work_contract_v1",
  "task_id": "...",
  "lark_task_guid": "...",
  "task_type": "data_correctness|ui_regression|api_contract|general_change",
  "repos": ["uvisa-admin"],
  "branch_namespace": "work/uvisa-lark-loop/<guid>",
  "target_surface": "...",
  "viewport": {"width": 1512, "height": 982, "label": "14-inch-admin"},
  "acceptance_atoms": [
    {
      "id": "A-source-to-sink-equality",
      "type": "data_correctness",
      "target_surface": "...",
      "requirement": "统计/KPI/total/badge 等展示值必须与源列表/API 在同一筛选条件下相等。",
      "proof_type": "source_to_sink_equality",
      "required_runtime_kinds": ["network", "dom", "trace"],
      "required_artifacts": ["captured_source_value", "captured_sink_value", "assertion_json"],
      "fail_closed_if_missing": true
    }
  ]
}
```

Task type mapping:

- `data_correctness`: target-surface atom + `A-source-to-sink-equality`，必须有同筛选条件 source/sink value capture + assertion JSON。
- `ui_regression`: target-surface atom + `A-ui-regression`，必须 1512x982 线上截图/DOM/trace。
- `api_contract`: target-surface atom + `A-live-api-contract`，必须真实登录态 request/response + schema assertion。
- Navigation/form/a11y keywords 自动追加 `A-navigation` / `A-form-flow` / `A-a11y`。

## 5. 本次已落地

Added:
- `/Users/charles/.hermes/scripts/uvisa_lark_work_contract.py`
- `/Users/charles/.hermes/scripts/test_uvisa_lark_work_contract.py`

Verified:
- `/Users/charles/.hermes/hermes-agent/venv/bin/python3 -m pytest -q scripts/test_uvisa_lark_work_contract.py scripts/test_lark_task_closeout_guard.py`
- Result: `15 passed in 0.10s`

Demo fail-closed:
- Generated demo contract for 08235149-like data correctness task.
- `closeout-check` blocked without atom proof mapping, PR URL, merge commit, online evidence, Lark response, TG notification, evidence dir.

## 6. 下一步 wiring（同一工程 PR 内继续）

1. Intake wiring：Lark task inserted/enriched into taskpool 时调用 `uvisa_lark_work_contract.py generate`，把 contract path 写入 task note frontmatter。
2. Scheduler wiring：claim 前读取 contract，按 `repos + branch_namespace + target_surface` 设置 conflict group、worktree path、allowed write boundary。
3. AgentTeam wiring：`delegate_to_worker` 改为 lease/result-manifest 模式；cycle 只 dispatch，不同步等待 worker 完整执行。
4. Closeout wiring：worker output 只进入 `worker_done_pending_proof`；controller 用 `closeout-check` + 现有 `lark_task_closeout_guard.py` 双门推进。
5. Merge queue wiring：同 repo PR 串行 rebase/merge；merge 后触发线上 14-inch browser harness 回归。
6. Notification wiring：`tg_notified` 必须记录 target、message id/status、evidence_dir，缺失不允许 done。

## 7. 安全原则

- 不自动清理 human_escape；先让新 contract/gate 阻断假完成。
- 不在当前脏主工作区直接切分支；先用 worktree 和 merge queue。
- 不把本地路径写进 Lark 评论；Lark 只写外部可用 PR/commit/deploy/online URL 摘要。
- TG 可以带本地 evidence_dir，因为是发给用户本人；done gate 要求 TG 已发送或记录明确通知 blocker。
