# Hermes 做梦机制：理论支点、多模型会商与架构完善方案

生成时间：2026-06-04
范围：Hermes nightly autonomous evolution / dreaming / sleep-time consolidation
状态：研究-架构综合稿。引用元数据部分已通过 Crossref 检索核验；模型意见不是事实证明，后续落地仍需代码级 evidence bundle 与 verifier。

## 1. 问题定义

当前 Hermes “做梦机制”不应被理解为“凌晨 cron 跑一个脚本”，而应定义为：

> 在低干扰窗口中，对白天产生的任务轨迹、失败、用户纠偏、技能变更、运行时告警、模型分歧和证明日志进行重放、模拟、评估、压缩、巩固和降噪，并把被验证的知识增量写回 canonical state / skills / memory / taskpool policy 的闭环控制系统。

核心成功条件：
- 不是 cron exit 0；
- 不是 dashboard 刷新；
- 不是多模型同意；
- 而是 effective state advancement + proof + rollback handle + dashboard 可追踪。

## 2. 多模型会商摘要

参与模型：
- Claude Opus 4.7：强调 CLS、replay、wake-sleep、proof gate、安全门禁；认为根因是 verifier_gap + SSOT 缺失。
- GPT-5.5：强调 canonical dream SSOT、readonly fail-closed、prioritized replay、sandbox evaluator、tiered consolidation；提醒当前 evidence_bundle.grounding 为空，不能把模型共识当真值。

一致点：
- 做梦机制必须先有 canonical SSOT。
- archived/read-only fallback 只能作为历史/迁移输入，不能计为成功。
- 夜间成功必须由 effective_state_before/after + proof_hash 判断。
- 选择层必须从固定扫盘改为 prioritized replay + cooldown + novelty gate。
- 生成候选与评估/巩固必须分离。
- 多模型分歧必须进入 dissent ledger，不可平均掉。

分歧/侧重：
- Claude 更偏“理论机制直接映射到模块”：CLS、replay、proof gate、safety gate。
- GPT 更偏“治理与可审计状态机”：ledger、fail-closed、tier policy、dashboard/proof。
- 采纳策略：以 GPT 的 governance ledger 做骨架，以 Claude 的认知机制映射填充选择/重放/巩固策略。

## 3. 关键理论支点与 Hermes 设计原则

### 3.1 Complementary Learning Systems, CLS

核心著作：
- McClelland, McNaughton, O'Reilly, 1995, “Why there are complementary learning systems in the hippocampus and neocortex”, Psychological Review, DOI 10.1037/0033-295x.102.3.419。

核心论点：
- 快速 episodic 学习与慢速 semantic consolidation 需要分离；快速系统捕获具体经验，慢速系统逐步整合抽象知识，避免 catastrophic interference。

迁移到 Hermes：
- 白天 session/task/tool trace 是 episodic memory。
- 夜间 skill/memory/policy 更新是 semantic consolidation。
- 禁止把一次失败直接写成全局规则；必须先进入 replay buffer，经多次证据或高置信 proof 才 promote。

指标：
- promotion_precision：被提升为 skill/memory/policy 的经验，在后续 N 次触发中仍有效的比例。
- premature_promotion_rate：单一事件未经足够验证就写入长期记忆/skill 的比例。

### 3.2 Sleep-dependent memory consolidation

核心著作：
- Diekelmann & Born, 2010, “The memory function of sleep”, Nature Reviews Neuroscience, DOI 10.1038/nrn2762。
- Walker & Stickgold, 2004/2007, sleep-dependent learning and memory consolidation。

核心论点：
- 睡眠不是被动存档，而是离线重放、重组和选择性巩固。

迁移到 Hermes：
- dreaming 不应全量扫盘；应选择高价值 replay items：失败、高影响、反复纠偏、模型分歧、用户明确偏好、验证缺口。
- 夜间要做 recombination：把多个相似 bad case 合成更一般的 skill/protocol，而不是逐条记忆。

指标：
- high_value_replay_coverage：高价值事件被夜间处理覆盖率。
- consolidation_yield：每次夜审产生的有效 skill/memory/test 增量数。

### 3.3 Synaptic Homeostasis Hypothesis

核心著作：
- Tononi & Cirelli, 2003, “Sleep and synaptic homeostasis: a hypothesis”, Brain Research Bulletin, DOI 10.1016/j.brainresbull.2003.09.004。

核心论点：
- 清醒期突触普遍增强，睡眠期做全局归一化/降噪，保留强信号，削弱噪声。

迁移到 Hermes：
- dreaming 不只“加知识”，也要删除/降权/合并/冷却：重复失败、过时记忆、低价值 taskpool 候选、冲突 skill、孤立规则。
- 对 apple skill 反复审计不前进这类现象，应触发 cooldown，而不是继续强化错误优先级。

指标：
- duplicate_stuck_audit_rate：重复审计同一无进展对象的比例。
- stale_memory_prune_rate：过时/冲突记忆被降权或清理的比例。

### 3.4 Dyna：learning / planning / acting 一体化

核心著作：
- Sutton, 1991, “Dyna, an integrated architecture for learning, planning, and reacting”, DOI 10.1145/122344.122377。

核心论点：
- 真实经验更新模型；模型可生成模拟经验；行动、规划、学习共享同一个状态模型。

迁移到 Hermes：
- 白天真实工具调用和夜间模拟评估必须写同一 canonical state。
- dreaming 可在 sandbox 中模拟 skill patch / memory change / routing policy，但只有 verifier 通过后才巩固。

指标：
- model_state_consistency_rate：dashboard、cron、nightly、taskpool 看到的状态一致率。
- simulation_to_real_success_rate：夜间模拟通过的改动，白天真实执行仍通过的比例。

### 3.5 Experience Replay / Prioritized Replay

核心著作：
- Lin, 1992, “Self-Improving Reactive Agents Based on Reinforcement Learning, Planning and Teaching”, Machine Learning。
- Schaul et al., 2015, “Prioritized Experience Replay”。

核心论点：
- 经验不应 FIFO 全量回放；高 TD-error / 高价值 / 高不确定经验应优先重放。

迁移到 Hermes：
- replay priority = impact × failure_severity × recurrence × novelty × verifiability ÷ cost。
- 重复无进展项必须 cooldown；有模型 dissent 的项要进入 targeted replay。

指标：
- mean_attempts_until_resolution：问题从首次失败到被稳定修复的平均尝试次数。
- replay_budget_efficiency：单位夜间预算带来的有效状态推进数。

### 3.6 Wake-Sleep Algorithm

核心著作：
- Hinton, Dayan, Frey, Neal, 1995, “The Wake-Sleep Algorithm for Unsupervised Neural Networks”, Science, DOI 10.1126/science.7761831。

核心论点：
- wake 阶段基于真实数据调整生成模型；sleep 阶段用生成样本训练识别模型；生成与识别角色不同。

迁移到 Hermes：
- generator 负责提出候选改动；evaluator 负责拒绝/验证；consolidator 负责写回。
- 同一个模型不能同时生成、证明并批准自己的改动。

指标：
- evaluator_rejection_accuracy：evaluator 拒绝的候选中，后续确认确实不应巩固的比例。
- generator_evaluator_independence：生成模型与评估模型/规则的分离程度。

### 3.7 DreamCoder / wake-sleep library learning

核心著作：
- Ellis et al., 2021, “DreamCoder: bootstrapping inductive program synthesis with wake-sleep library learning”, PLDI, DOI 10.1145/3453483.3454080。

核心论点：
- 通过解决任务、压缩可复用程序片段、再生成新任务/样本，形成可解释的 library learning。

迁移到 Hermes：
- skill 不是日志堆积，而是 library abstraction。
- 多个 bad case 只有带来压缩收益和泛化验证，才应沉淀为 skill。

指标：
- library_compression_gain：新 skill/protocol 是否减少后续 prompt/tool 步骤或重复错误。
- skill_reuse_success_rate：沉淀 skill 后被正确触发并成功复用的比例。

### 3.8 Reflexion / Self-Refine / Voyager / Generative Agents

核心著作/系统：
- Reflexion, 2023, language agents with verbal reinforcement learning。
- Self-Refine, 2023, iterative refinement with self-feedback。
- Voyager, 2023, open-ended embodied agent with skill library。
- Generative Agents, 2023, memory stream + reflection + planning, DOI 10.1145/3586183.3606763。

核心论点：
- Agent 可以通过反思、记忆流、技能库和自反馈改进长期行为。

迁移到 Hermes：
- 反思只能产生 candidate；不能直接等于 truth。
- memory stream 需要 importance/recency/relevance 检索，但写入长期记忆必须过 hygiene gate。
- skill library 要可测试、可回滚、可度量。

指标：
- hallucinated_learning_rejection_rate：被 verifier 拦截的幻觉式学习比例。
- reflection_to_patch_precision：反思建议最终成为有效 patch 的比例。

### 3.9 Gödel Machine / POWERPLAY

核心著作：
- Schmidhuber, Gödel Machines, 2006/2007。
- Schmidhuber, POWERPLAY, 2011/2013, DOI 10.3389/fpsyg.2013.00313。

核心论点：
- 自我修改需要证明会提升目标函数；系统可通过寻找最简单尚未解决的问题逐步扩展能力。

迁移到 Hermes：
- 自改必须 proof-backed：pre/post metric、rollback、blast radius、kill switch。
- dreaming 应维护 “未解决但最小可验证问题池”，而不是随意优化。

指标：
- proof_backed_self_change_rate：带 proof/rollback 的自改比例。
- simplest_unsolved_resolution_rate：最小未解问题被逐步解决的比例。

### 3.10 Cybernetics / Requisite Variety / PDSA / Double-loop learning / Meta-synthesis

核心著作/论点：
- Wiener, Cybernetics, 1948：控制与通信闭环。
- Ashby, Introduction to Cybernetics, 1956：必要多样性。
- Deming, PDSA：计划-执行-研究-行动循环。
- Argyris & Schön：single-loop / double-loop organizational learning。
- 钱学森综合集成：专家体系、机器体系、知识体系、总体设计部的分层综合。

迁移到 Hermes：
- single-loop：补 Example、修路径。
- double-loop：修改 selector/evaluator/policy，避免同类失败。
- meta-synthesis：source/evidence、model dissent、engineering verification 三本账分离。

指标：
- double_loop_fix_ratio：修机制而非只修个案的比例。
- dissent_retention_rate：模型/证据分歧被记录并进入决策的比例。
- control_loop_latency：错误从发生到被探测、修复、验证、沉淀的周期。

## 4. 当前 Hermes 做梦机制缺口诊断

### 4.1 数据层缺口

缺 canonical Dream/Evolution SSOT。旧 confidence-db / results.tsv 位于 skill 包内，随 skill archive 消失。应迁移到：

`~/.hermes/state/dreaming/`

并由 resolver 统一访问。

### 4.2 选择层缺口

当前类似“低分 + 久未审计”选择，缺少：
- prioritized replay；
- novelty gate；
- cooldown；
- no-progress demotion；
- dissent priority；
- cost/verifiability 约束。

### 4.3 生成/模拟层缺口

当前 auto_fix_skill 是局部模板补丁器，缺少：
- sandbox simulation；
- dry-run；
- candidate diff；
- skill score replay；
- path writability proof；
- generator/evaluator 分离。

### 4.4 评估层缺口

cron exit 0 被当成功，缺少：
- effective_state_before/after；
- proof_hash；
- evaluator rejection reason；
- real verifier；
- independent model/tool check。

### 4.5 巩固层缺口

缺少分级巩固策略：
- T0 advisory only；
- T1 low-risk skill doc patch；
- T2 selector/evaluator script patch；
- T3 runtime/taskpool/router/policy change。

### 4.6 降噪层缺口

只会加/修，不会：
- 合并重复记忆；
- 冷却无进展审计；
- 移除 stale candidate；
- 降权冲突经验；
- 控制 skill/memory 膨胀。

### 4.7 安全与治理缺口

缺少：
- archived fail-closed；
- blast radius cap；
- rollback handle；
- proof log；
- dissent ledger；
- no secret retention；
- cost gate；
- human escalation threshold。

## 5. 完善后的 Hermes Dreaming 架构

### 5.1 数据层：Dream SSOT

路径：
- `~/.hermes/state/dreaming/canonical_state.jsonl`
- `~/.hermes/state/dreaming/replay_buffer.jsonl`
- `~/.hermes/state/dreaming/proofs/`
- `~/.hermes/state/dreaming/rollbacks/`
- `~/.hermes/state/dreaming/dissent.jsonl`
- `~/.hermes/state/dreaming/metrics.json`

每条 run ledger 至少包含：
- run_id
- input_snapshot_hash
- selected_items
- replay_priority
- candidate_changes
- simulated_outputs
- evaluator_result
- consolidation_commit
- effective_state_before
- effective_state_after
- proof_hash
- dissent
- rollback_handle
- cost
- tier
- status: OK | WARN | ERROR | ADVISORY_ONLY

### 5.2 选择层：Prioritized Replay Selector

输入：
- session failures
- tool errors
- user corrections
- skill audit gaps
- memory hygiene alerts
- taskpool stuck events
- cron/gateway/runtime incidents
- multi-model dissent

优先级公式草案：

priority = (impact * recurrence * severity * novelty * verifiability * dissent_weight) / (cost * risk * recent_attempt_penalty)

必须有：
- max_same_target_per_window
- cooldown_until
- no_progress_count
- unresolved_gap_class
- alternative hypothesis sampling

### 5.3 生成/模拟层：Sleep Sandbox

流程：
1. candidate generator 提出改动。
2. sandbox 应用到临时副本。
3. 执行 schema/lint/test/path-writable/effective-diff 检查。
4. 产出 proof bundle。
5. evaluator 独立判定。

候选类型：
- skill Example/Checkpoints 修复；
- memory 合并/删除建议；
- taskpool policy tweak；
- selector 权重调整；
- dashboard 指标补充；
- runtime issue candidate。

### 5.4 评估层：Verifier/Evaluator

成功必须满足：
- 有目标 SSOT；
- 非 archived write；
- 有 before/after 差异；
- 有 verifier 通过；
- 有 rollback；
- 有 dashboard 记录；
- 若多模型参与，dissent 被保留。

### 5.5 巩固层：Tiered Consolidation

T0：只写诊断/proof/replay buffer，不改长期状态。
T1：低风险 skill 文档/Example patch，可自动应用但必须回读验证。
T2：selector/evaluator/script 调整，需要测试与 scoped commit。
T3：runtime/router/taskpool/memory policy 大改，需要多证据、多模型、人工或更高门禁。

### 5.6 降噪层：Synaptic Downscaling

夜间必须执行：
- duplicate candidate merge；
- stale memory detection；
- repeated no-progress cooldown；
- low-value replay eviction；
- old proof compaction；
- conflicting skill warning。

### 5.7 安全门禁

强制规则：
- archived 只读；
- no secrets retention；
- no stealth / Cloudflare bypass；
- no external scraper as core dependency；
- no cross-profile write by default；
- high blast radius 需人工/更高 tier；
- rollback mandatory；
- budget cap mandatory。

### 5.8 Dashboard / Proof Log

Dashboard 不显示“cron ok”作为成功，而显示：
- last_effective_dream_at
- effective_state_advanced
- proof_attached_ratio
- rejected_candidates
- cooldown_targets
- no_progress_count
- archived_fallback_count
- write_blocked_count
- dissent_count
- rollback_count
- cost
- next_replay_queue

## 6. 反对意见与风险

1. 自我强化错误
- 风险：错误经验被反复 replay 并提升成规则。
- 防线：promotion requires independent proof + recurrence + rollback。

2. Hallucinated learning
- 风险：模型反思听起来合理但没有事实支撑。
- 防线：reflection 只能生成 candidate；truth gate 由工具/测试/证据负责。

3. 过拟合个人短期事件
- 风险：一次项目 incident 变成全局规则。
- 防线：抽象层级标注：事件/项目事实/场景规则/全局门禁/ADR/元规则。

4. Drift / 无监督自改
- 风险：系统持续改自己导致不可解释漂移。
- 防线：tiered consolidation + scoped commit + rollback + dashboard。

5. 成本失控
- 风险：夜间多模型 replay 太多。
- 防线：priority budget、T0/T1 默认低成本、本地 verifier 优先。

6. 隐私与权限
- 风险：session/tool trace 含敏感信息。
- 防线：redaction、proof hash、最小必要摘录、不保存 secret。

7. 假健康
- 风险：cron ok 但没有进化。
- 防线：success = effective state advancement，不是 exit 0。

## 7. 90 天路线图

### P0：止血与定义成功语义（0-2 周）

目标：修掉假成功，建立 Dream SSOT 最小骨架。

交付：
- `~/.hermes/state/dreaming/canonical_state.jsonl`
- archived fail-closed guard
- nightly 输出 effective_state_before/after
- apple 重复审计 cooldown 或 Example 修复
- dashboard 显示 effective dream health

验收指标：
- archived fallback 不再计为 OK。
- cron ok 与 dashboard DEGRADED 不再分裂。
- 连续 3 次无进展不会重复审计同一 target。
- 每次 nightly 至少产生 run_id + proof/advisory reason。

### P1：Replay buffer + selector（2-4 周）

目标：从扫盘变为 prioritized replay。

交付：
- replay_buffer.jsonl
- priority scorer
- cooldown/novelty/no-progress gate
- target class taxonomy

验收指标：
- high_value_replay_coverage >= 80%。
- duplicate_stuck_audit_rate 下降到 < 5%。
- replay item 均有 target SSOT 和 verifier path。

### P2：Sleep sandbox + evaluator（4-8 周）

目标：生成/模拟/评估/巩固分离。

交付：
- candidate generator interface
- sandbox dry-run
- independent evaluator
- proof bundle schema
- rollback manifest

验收指标：
- proof_attached_ratio >= 95%。
- hallucinated_learning_rejection_rate 可观测。
- low-risk skill patch 自动回读验证通过率 >= 90%。

### P3：Double-loop / meta-synthesis dreaming（8-12 周）

目标：做梦机制从修个案升级到修机制。

交付：
- double-loop classifier
- dissent ledger
- tiered consolidation policy
- memory/skill/taskpool/routing 联合 replay
- monthly dream review report

验收指标：
- double_loop_fix_ratio 持续上升。
- promotion_precision >= 85%。
- rollback_count 可追踪且低于阈值。
- dashboard 能回答：昨夜学到了什么、拒绝了什么、为什么拒绝、如何回滚。

## 8. 可立即转任务池的实现任务

1. 建立 canonical Dream SSOT 与 run ledger schema。
2. 修改 nightly/no-agent success semantics：exit 0 不等于 success。
3. 增加 archived readonly fail-closed guard。
4. 增加 replay selector 的 cooldown/no-progress gate。
5. 增加 skill Example fixer 或 unsupported_gap ledger，解除 apple 重复审计。
6. 建立 proof bundle + rollback manifest。
7. dashboard 接入 effective dream health。
8. 增加 hardcoded path lint，禁止旧 confidence-db/results.tsv 路径扩散。

## 9. 结论

Hermes 做梦机制的最终形态，不是“夜间自动修 skill”的脚本，而是一个类睡眠的闭环学习系统：

- CLS 决定快慢学习分层；
- sleep consolidation 决定离线重放与巩固；
- synaptic homeostasis 决定降噪和遗忘；
- Dyna / replay 决定经验选择和模拟；
- wake-sleep / DreamCoder 决定生成-评估分离与知识库压缩；
- Reflexion/Voyager/Generative Agents 提供 agent 记忆与技能库参考；
- Gödel/POWERPLAY 提供自改证明和逐级挑战；
- cybernetics/PDSA/double-loop/钱学森综合集成提供治理与多脑证据账。

工程上的第一性原则：

> 每一场梦都必须留下可验证的 run ledger；每一次巩固都必须有 proof；每一次拒绝都必须有 reason；每一次自改都必须可回滚；每一次多模型分歧都必须被保留；每一次成功都必须体现为 canonical state 的有效推进。
