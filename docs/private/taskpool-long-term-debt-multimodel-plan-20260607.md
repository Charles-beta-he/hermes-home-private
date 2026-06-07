# Taskpool 长期债务多模型治理方案（2026-06-07）

## 当前基线

- Unified health: 95/100，Cron Health YELLOW；直接原因是 `envelope-executor-cycle` 上次脚本超时。
- 手动运行 `envelope_executor_run_1.py` 可成功退出，且 cron job 手动 `run` 后 `last_status=ok`。
- Taskpool: total=256；active=9；done=196；archived=51；review=5；retry≈1-2；blocked=2；pending=0；claimed=0；dispatchable=0。
- `next --json`: no dispatchable local-brain tasks。
- `selfcheck --json`: PASS；`proof-check --json`: PASS，但 warning=75。
- Proof debt: terminal mission envelope debt=67；terminal invalid autorun proof hash debt=8。
- Envelope bus: total≈614；terminal debt≈155；since_ack failure=1；human_escape=false；live RUNNING=1。
- Continuation: active=101；archived=3433；scope=conversation；当前 GC 只处理 active older than 7d，因此无动作。
- Handoff backlog: ≈80-81，低于 100 阈值。
- Experience Ratchet: validate OK，checked=13。

## 多模型共识

### Claude / 架构仲裁

1. 当前不是主链崩溃，而是 runtime blocker、历史治理 debt、容量治理 backlog 被混在一个健康叙事里。
2. Cron 只能作为 watchdog/summary/cleanup，不能作为主执行语义；主链应事件驱动。
3. 历史 proof debt 必须可见、可统计、可分批清理，但不能阻断无关 dispatchable P1。
4. Continuation/handoff backlog 是生命周期治理，不应按年龄粗暴删除。
5. 禁止通过降低 proof/multimodel gate、批量 ack/delete DB、伪 done 来换健康分。

### DeepSeek / 工程实现

1. 先补只读 debt ledger，把 envelope/proof/continuation/handoff 放到同一 JSON 视图。
2. 修 legacy `envelope_executor.py`：支持 fenced/multiline `PROOF_JSON`，并让 worker timeout 落在 cron wall-clock 内，避免 cron unstructured timeout。
3. Continuation GC 后续从 age-only 升级为 age + cap + per-task compaction，但第一阶段先只读/分桶。
4. Proof debt 只能迁移已有 Proof Log / artifact，不得补造 proof/hash。
5. `v_state` 后续应区分 post-ack live failure 与 historical terminal debt，避免健康分长期被历史 FAILED/BLOCKED 拉低。

### MiMo / AI 自进化治理

1. 自动化分层：L0 只读观测；L1 可逆机械规范化；L2 bounded execution；L3 策略/生命周期需多模型/人工；L4 不可逆/外部副作用默认禁止自动化。
2. Review/retry/blocked 必须区分控制面健康证据、交付证据、治理证据；`py_compile`/`proof-check PASS`/`discussion_result.json` 不等于 feature delivered。
3. `child done != parent ratified`；blocked parent 仍需 parent-level ratification refresh 或 economy gate 保持 blocked。
4. Continuation backlog 不能以 count 清零作为 KPI；要按 actionable/stale/duplicate/human-needed 分桶。
5. 手动成功不能替代 cron 成功；cron 需要证明 scheduler 环境、timeout、stdout/stderr、幂等和 proof artifact。

## 决策矩阵

| 类别 | 当前数量/状态 | 自动化等级 | 下一步 |
|---|---:|---|---|
| envelope cron timeout | 1 broken cron, 手动 run OK | L1/L2 | 修 parser + bounded timeout；手动 run cron 清 last_status |
| post-ack envelope failure | since_ack failure=1 | L0/L1 | 分类，不 ack/delete，不触发 human_escape |
| proof debt | 75 warnings | L1 + 人工抽样 | 小批量迁移已有证据；禁止补造 |
| continuation backlog | active=101 | L0/L1 | 先 ledger 分桶；后续引用安全 GC |
| handoff backlog | 80-81 | L0/L1 | 低于阈值，保持报表/趋势 |
| review queue | 5 | L2/L3 | final-landed bundle 检查；不自动 done |
| retry queue | 1-2 | L1/L2 | 分类 timeout/missing proof/infra；到期后 bounded retry |
| blocked queue | 2 | L2/L3 | 子证据 backfill；parent ratification 保留多模型/人工 |
| dispatchability | 0 | N/A | 不调并发；先处理 review/retry/blocked |

## 已落地的低风险改动

1. 新增只读总账脚本：
   - `/Users/charles/.hermes/scripts/taskpool_debt_ledger.py`
   - 输出 `taskpool_debt_ledger_v1`，只读，不变更 task/cron/envelope/continuation/memory/skill/profile。

2. 修 legacy envelope executor 的明显缺口：
   - `/Users/charles/.hermes/scripts/envelope_executor.py`
   - `extract_proof()` 支持单行、fenced、多行 `PROOF_JSON`。
   - 默认 worker timeout=90s，wall budget=105s，避免 120s cron 边界无结构化 timeout。
   - 仍 fail-closed：无 proof 或 invalid proof 不会标 DONE。

3. 手动重新运行 cron：
   - `envelope-executor-cycle` last_status 已变为 `ok`。

## 后续执行顺序

1. P0：观察 envelope live RUNNING 是否正常收束；若变成 stale，再按 stale-running recovery，而不是 ack/delete。
2. P1：针对 review=5 跑 final-landed bundle audit，生成 close/requeue/block 建议，不自动 done。
3. P1：针对 retry=1-2 分类 timeout/missing_proof/infra，只有 stale/rerunnable 才 bounded retry。
4. P2：proof debt dry-run migration，每批最多 5 个，只迁移已有证据。
5. P2：continuation GC 升级为引用安全分桶：live / stale-recoverable / terminal-audit / disposable。
6. P3：`v_state` envelope scoring 区分 historical debt 与 since_ack live failures。

## 反例门

- 不把历史 proof warnings 隐藏成绿灯。
- 不把 `PASS_ADVISORY_ONLY` 或 multimodel discussion 当交付证据。
- 不把 `child done` 当 parent PASS。
- 不用更密集 cron 轮询替代事件驱动主链。
- 不直接清空 envelope FAILED/BLOCKED 或批量 ack escape。
- 不批量 archive/delete task 来清 warning。
- 不降低 proof/multimodel gate 换健康分。
