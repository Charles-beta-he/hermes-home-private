# Memory Cache / Recurrent Task State / Continuation Compaction SSOT（2026-06-07）

## 来源信号

用户提供微信视频号链接：`https://weixin.qq.com/sph/ASPvJFQnXb`。
可读页面标题：`重磅突破！谷歌推出内存缓存 RNN将终结 Transformer 时代，打破 AI 架构固有瓶颈`。

该视频本身未作为技术事实来源；标题只作为方向信号。所有 Hermes 落地仍以本地可验证脚本、任务池状态、proof gate 和回放 benchmark 为准。

## 设计判断

不要把长期能力押注在更大上下文窗口或“模型自己记住”。Hermes 应把长期任务能力拆成：

1. `working_context`：当前回合必需上下文，严格预算。
2. `recurrent_task_state`：任务级可回放状态，记录目标、已完成 evidence、当前 blocker、下一步 bounded action、禁止重复探索的 wrong-source hypothesis。
3. `memory_cache`：可重建的检索/缓存层，不是 SSOT；必须有 benchmark、schema、staleness/rejection gate 和 rollback。
4. `proof_artifacts`：交付证据和任务生命周期证据；不得被自然语言摘要替代。
5. `continuation_packet`：预算耗尽时的续跑包；应被压缩/分桶为 live、stale-recoverable、terminal-audit、disposable，而不是无限 active 堆积。

## 与当前长期债务的映射

当前 debt ledger 已显示：

- continuation active ≈ 101：需要引用安全分桶与压缩，不是粗暴清空。
- proof warnings ≈ 75：需要 structured evidence 迁移，不是把 body history 注入 prompt。
- envelope terminal debt ≈ 155：需要区分 historical terminal debt 与 post-ack live failures。
- taskpool review/retry/blocked：需要 parent-level ratification / final-landed bundle，而不是 child done 或 advisory PASS。

## 第一阶段落地边界（本轮）

允许：

- 扩展本地 deterministic memory replay gate fixture。
- 增加 token-cost / recurrent-state / continuation-compaction 相关 case。
- 产出 JSON 报告作为 proof artifact。
- 创建/更新 taskpool follow-through 任务，带明确 acceptance evidence。

禁止：

- 改核心记忆注入语义。
- 把视频标题当论文事实或架构事实。
- 自动替换 memory/profile/skill 内容。
- 批量清理 continuation active 包。
- 降低 proof/lifecycle/multimodel gates。

## 第一阶段验收

- `local_brain_memory_replay_gate.py` 默认 fixture 覆盖：
  - evidence-backed positive recall
  - noise/red-line rejection
  - temporal drift rejection
  - external memory claim rejection
  - recurrent task state compaction preference
  - token-cost prefilter rejection
- gate 输出包含 token budget evidence / compact-state evidence。
- `python3 ~/.hermes/scripts/local_brain_memory_replay_gate.py --json` PASS。
- taskpool 新增 follow-through 任务，引用本 SSOT 和 gate report。
- health/taskpool/ratchet 复测无回退。

## 已落地实现（2026-06-07）

- `~/.hermes/scripts/local_brain_memory_replay_gate.py`：默认 fixture 已覆盖 recurrent-state compaction 与 token-cost prefilter；compact state 被采纳，raw/full-history prompt 被 token budget 拒绝。
- `~/.hermes/scripts/continuation_compaction_manifest.py`：只读生成 continuation compaction dry-run manifest，按 `live` / `stale-recoverable` / `terminal-audit` / `disposable` 分桶，不执行删除或归档。
- `~/.hermes/scripts/continuation_compaction_apply.py`：独立 mutation tool，只消费已审阅 manifest；当前仅允许把 `active + disposable + task_status:done` packets 移入 archived，不删除，不碰 live/stale/terminal-audit。
- `~/.hermes/scripts/task_continuation.py`：续跑上下文新增 `hermes_recurrent_task_state_v1` compact resume state；保留原始 checkpoint，不把 compact state 伪装成 proof。
- 当前 manifest proof artifact：`~/.hermes/state/continuation-compaction-manifest-after-apply-20260607.json`。
- 当前 apply proof artifact：`~/.hermes/state/continuation-compaction-apply-20260607.json`；已归档 23 个 disposable active packets，active continuation 从 101 降至 78，未执行删除。

## 后续主线

1. 人工/多模型审阅 manifest 中 `terminal-audit` 与 `stale-recoverable` 桶，确认哪些可归档、哪些需要恢复、哪些应保留审计。
2. Memory cache gate：检索命中、staleness、wrong-source rejection、token saving、proof-linked use。
3. Recurrent task state：将更多 taskpool worker resume path 迁移到 compact state，禁止 full-history prompt 回退成为默认。
4. Continuation compaction：在人工批准后实现独立 mutation tool；mutation 必须消费已审阅 manifest，不能重新粗暴扫描删除。
5. Benchmark：比较 no memory / full history / retrieval memory / recurrent state / proof-linked cache 的成本、成功率、幻觉率、重复工作率。

## 反例门

- 更大上下文 ≠ 更好长期能力。
- 检索命中 ≠ 可用记忆；必须通过 staleness/proof/red-line gate。
- continuation 数量下降 ≠ 能力提升；必须证明 live work 未丢失。
- task 状态推进 ≠ 交付完成；必须有 feature-specific evidence。
