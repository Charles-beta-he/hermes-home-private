# Taskpool 高并发 / 高自动化链式自运行棘轮升级方案（2026-05-24）

## 0. 当前证据基线

实测命令基线：

- `brain_task_orchestrator.py list --json`
  - active=43
  - retry=1, running=1, claimed=24, blocked=1, review=2, pending=14
  - lane=work:43
- `brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 24 --json`
  - status=OK
  - selected_count=0
- `brain_task_orchestrator.py selfcheck --json`
  - PASS
  - warning: autorun handoff directory has 125 handoffs
- `brain_task_orchestrator.py evidence-spine --json`
  - OK / PASS
- `brain_task_dispatch_tick.py --summary --no-state`
  - OK, error_count=0, dispatchable=true, parallel_selected=0

解释：当前不是“没有任务”，也不是 proof gate 全局坏掉；真实瓶颈是 claim-bound backlog / execution starvation：claimed=24 但 running=1，导致并发 dry-run 没有额外 boundary-safe slot 可派发。

## 1. 多模型咨询证据

本轮真实多模型 fan-out：

- tick dir: `/Users/charles/.hermes/tick-20260524-121840-812060-p63724-6015ddb5-c69f234a`
- planners:
  - `gpt-5.5`
  - `claude-opus-4-7`
  - `mimo-v2.5-pro`
- merged_plan: `/Users/charles/.hermes/tick-20260524-121840-812060-p63724-6015ddb5-c69f234a/merged_plan.json`
- note: consult run exceeded parent command timeout during discussion/consensus, but three model plans and merged plan were written successfully. Treat as advisory multi-model evidence, not final truth certification.

共识摘要：

1. 先观测，后提并发。
2. claimed=24/running=1 是执行饥饿，不是简单 max_agents 太小。
3. agent_team_controller 的同步 claim+execute cycle 是高并发化前必须拆开的关键点。
4. dynamic_runner / dispatch_tick / event_next_tick 的正确分层必须保持：
   - safe tick 可读/协调；
   - explicit autorun 才能 claim/handoff；
   - event_next_tick 只做 review-close + next dry-run，不递归 claim；
   - worker 不能 done，done 只能 proof-gated closeout。
5. 棘轮升级顺序必须是 P0 telemetry/reaper → P1 claim/execute split → P2 bounded worker pool/concurrency raise → P3 compaction/dashboard polishing。

## 2. 架构目标

目标不是“把 max_agents 调大”，而是把任务池升级成一个有界、自恢复、可审计的执行系统：

```text
Collector / Intake
  -> canonical Markdown task note
  -> dispatch tick telemetry / governance gates
  -> parallel dry-run boundary selection
  -> claim-only enqueue
  -> worker executor pool with heartbeat
  -> proof artifact
  -> review
  -> proof-gated auto-close done
  -> bounded next-tick follow-through (depth<=3, no recursive claim)
```

关键不变量：

- Markdown task body 永远不是脚本。
- Worker 只能推进到 running/review/retry/blocked，不能直接 done。
- done 必须经过 proof-gated closeout。
- 链式触发必须有界，max depth <= 3。
- 不递归 claim；不在一个 tick 中无限执行。
- Work/Product P0/P1 不被 self-evolution 饿死。
- Project code 默认不 push。
- 未知状态 fail-closed，历史 proof debt warn-visible 但不阻塞独立安全派发。

## 3. 棘轮实施层级

### P0-A：Claim-state / starvation telemetry（最低风险第一补丁）

落点：`scripts/brain_task_dispatch_tick.py`

新增只读 telemetry，不改变派发行为：

```json
{
  "claim_state": {
    "claimed_total": 24,
    "running_total": 1,
    "review_total": 2,
    "pending_total": 14,
    "stale_claim_count": 0,
    "unsafe_unknown_claim_count": 0,
    "claimed_running_ratio": 24.0,
    "execution_starvation": true,
    "parallel_selected_count": 0,
    "handoff_backlog_count": 125,
    "proof_gate_status": "PASS"
  }
}
```

Fail-closed gate：只要 telemetry 缺失/格式坏/depth>3/recursive claim attempt/proof gate FAIL，则拒绝 concurrency raise；普通 backlog/历史 warning 仅 warn-visible。

验收：

- `python3 scripts/test_brain_task_dispatch_tick.py`
- `python3 -m py_compile scripts/brain_task_dispatch_tick.py`
- `python3 scripts/brain_task_dispatch_tick.py --summary --no-state`
- summary 中存在 `claim_state`，且当前基线识别 `execution_starvation=true`。

### P0-B：Stale claim / lease / heartbeat classifier

落点：`scripts/brain_task_orchestrator.py` + `brain_task_dispatch_tick.py`

先分类，不急着自动释放：

- `live_claim`: claim 未过期，有 running/heartbeat/proof activity。
- `stale_reclaimable`: claim 过期且无心跳、无活跃 proof artifact。
- `unsafe_unknown`: 数据不足，不自动回收，只告警。

后续才允许 `--reap-stale-claims` 写路径，且每个 transition 必须带结构化 evidence。

### P1：agent_team_controller claim/enqueue 与 execute 分相

落点：`scripts/agent_team_controller.py`

新增两个明确子命令：

- `claim-cycle --max-claims N --wall-budget-seconds 20`
  - 只 claim + create envelope + enqueue。
  - 不调用 `hermes chat`。
  - 不调用 delegate。
  - cron-safe。
- `execute-cycle --max-workers N --wall-budget-seconds M`
  - 读取 envelope queue。
  - worker heartbeat。
  - 写 proof artifact。
  - 只 transition 到 review/retry/blocked。

保留原 `cycle`，但逐步降级为 wrapper 或 deprecated safe path。

### P2：Bounded worker pool / execution slot budget

落点：`taskpool_dynamic_runner.py` + `agent_team_controller.py`

并发预算不再只看 `selected_count`：

```text
execution_free_slots = max_workers - live_running - live_worker_processes
claim_free_slots = max_claims - live_claims_non_stale
```

只有当：

- proof/evidence gate PASS；
- stale_claim_count 不上升；
- handoff backlog 在阈值内或 compaction 正常；
- worker_spawn_success_rate 健康；
- P0/P1 work starvation 秒数未超阈值；

才允许从 N=1 → N=2 → N=3 → N=6 棘轮提升。

### P3：Handoff backlog compaction + dashboard

落点：`brain_task_dispatch_tick.py` 或独立 maintenance script。

当前 125 handoffs 不是硬阻塞，但会让控制面变钝。保留最近 50，老文件归档到 ledger，不直接删除。

## 4. 任务池落地分解

依赖顺序：

1. P0-A telemetry
2. P0-B classifier / recovery gate
3. P1 claim-execute split
4. P2 worker-pool ratchet
5. P3 compaction/dashboard

每个任务都必须带：

- capability_delta
- anti_drift_check
- acceptance_evidence
- dependency_order
- multimodel evidence artifact

## 5. 反失控门

硬门：

- depth > 3 => ERROR / no execution
- recursive claim attempt inside event_next_tick => ERROR
- worker direct done attempt => reject
- proof gate FAIL => no review->done
- unknown lease state => no auto-reap
- kill switch present => no claim/execute

软门：

- historical proof debt
- handoff backlog warning
- advisory-only multimodel PASS
- weak consensus advisory plan

软门必须可见，但不应冻结安全的 P1 work dispatch。
