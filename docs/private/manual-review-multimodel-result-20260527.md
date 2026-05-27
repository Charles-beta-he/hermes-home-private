# 人工复核任务多模型复核结果 — 2026-05-27

## 运行证据

- 输入包: `/Users/charles/.hermes/docs/private/manual-review-multimodel-packet-20260527.md`
- 首轮完整证据包运行: `/Users/charles/.hermes/tick-20260527-075316-449478-p11464-dc0a39f9-5a226f25/`
  - Claude 给出有效复核；GPT timeout；MiMo parse fail；结论降级。
- 二轮压缩上下文 T1 fanout: `/Users/charles/.hermes/tick-20260527-080435-673130-p16775-8c76b5a0-16cb4c0e/`
  - 参与: Claude Opus 4.7, GPT-5.5, MiMo 2.5 Pro, DeepSeek V4 Pro
  - fanout quorum met: 3/4 succeeded, min 2
  - consensus: weak_consensus, but核心结论一致：不能把 done/advisory/py_compile/hash/ExperienceAtom 当最终落地。

## 总结结论

多模型没有认证任何一个任务为 `FINAL_LANDED`。

原因：当前证据对大多数任务只证明“分析/评估/原子提取/阶段性 spike/候选方案”完成，缺少 final-adoption 所需的 commit、skill/script/config、测试、benchmark、read-back 或真实集成证据。

审批口径建议：

- `approve_reopen`: done 不诚实或 P1/P2 高风险，需回任务池继续 prototype/benchmark/adopt-update。
- `approve_watch`: 确认是拒绝/观察/纠错完成，不进入集成。
- `approve_close_as_partial`: 允许关闭为“阶段性成果已完成”，但不得宣传为最终集成。
- `needs_more_evidence`: 可能已落地，但证据不足；审批前先补 commit/产物/验证证据。

## 待你审批的建议表

| ID | 任务 | 多模型复核分类 | 建议审批动作 | 理由 |
|---|---|---|---|---|
| T01 | 审计 Hermes 内置技能体系并优化开箱即用基础能力 | PARTIAL_STAGE / needs evidence | needs_more_evidence | 有 implementation/test 信号，但同时有 not_certified/advisory；需确认 skill patch/commit/read-back。 |
| T02 | budget exhaustion grace-call / continuation / new-session resume | REOPEN_FOR_TASKPOOL | approve_reopen | P1；Claude 明确指出 not_certified/round failed/gate FAIL yet done，是最高优先级 fail-closed 风险。 |
| T03 | Anthropic Founders Playbook → 单人公司/多-agent运营画像 | PARTIAL_STAGE | approve_close_as_partial | 主要是组织模型/运营画像映射与 follow-up 顺序；无最终集成证据。 |
| T04 | AI 编码后置 CI/CD → 内嵌连续验证/预合并层 | REOPEN_FOR_TASKPOOL | approve_reopen | P1；acceptance 要 selfcheck/test/状态机证据，但证据只有 advisory/阶段信号。 |
| T05 | 日报补 TrendRadar 源质量评估与接入边界 | NEEDS_MORE_EVIDENCE | needs_more_evidence | deterministic 认为 likely-landed，但多模型指出 py_compile/hash 不足；需证明实际日报配置/字段已接入。 |
| T06 | CLI-Anything / CLI-Hub 工具注册表与 agent-native 适配 | NEEDS_MORE_EVIDENCE | needs_more_evidence | 有 implementation/test 信号，但需确认 net-new registry/permission/script/config 落地。 |
| T07 | AgentMemory isolated MCP compatibility spike | PARTIAL_STAGE | needs_more_evidence 或 approve_close_as_partial | spike 可算阶段性；若要 final，需要 health/tools/list/remember-recall/cleanup 证据。 |
| T08 | AgentMemory governance selfcheck | PARTIAL_STAGE / maybe reopen | needs_more_evidence | 需确认 selfcheck 脚本、三态输出、proof-check 是否真实存在；否则不能最终关闭。 |
| T09 | Experience Ratchet baseline source freshness matrix | REJECT_OR_WATCH / PARTIAL_STAGE | approve_watch | 矩阵/新鲜度基线，不是 core/memory 直接集成；可作为治理/观察产物关闭。 |
| T10 | AgentMemory ExperienceAtom extraction | PARTIAL_STAGE | approve_close_as_partial | ExperienceAtom 提取是阶段性沉淀；anti_drift 明确 no direct AgentMemory integration。 |
| T11 | Bytebot ExperienceAtom extraction | PARTIAL_STAGE | approve_close_as_partial | 原子提取，不代表 computer-use/external-control 已落地。 |
| T12 | Karpathy skills ExperienceAtom extraction | PARTIAL_STAGE | approve_close_as_partial | 原子提取，不代表 coding guardrails 已实际采用。 |
| T13 | OpenClaw wrong-source supersede atom | REJECT_OR_WATCH | approve_watch | wrong-source/supersede 是纠错/撤销类完成，不是集成。 |
| T14 | Hermes upstream ratchet atom extraction | PARTIAL_STAGE | approve_close_as_partial | 原子提取；anti_drift 禁止 auto-promote private/main。 |
| T15 | RAG-Anything atom extraction | PARTIAL_STAGE | approve_close_as_partial | 原子提取，不代表 typed manifest / proof markdown 已接入。 |
| T16 | cross-repo consensus synthesis | PARTIAL_STAGE | approve_close_as_partial | proposal/candidate synthesis，不等于 promoted/landed。 |
| T17 | Karpathy-style negative-space evals | REOPEN_FOR_TASKPOOL | approve_reopen | P1；需要真实 eval fixtures + pytest/read-back，当前证据不足，不能 final。 |
| T18 | Karpathy examples.md → optional behavior evals | PARTIAL_STAGE / needs evidence | needs_more_evidence | 可能有 optional fixtures，但需确认 >=4 behavior classes、expected outcome/read-back。 |
| T19 | 长任务管理四原则 → taskpool handoff/evaluator governance | PARTIAL_STAGE / maybe reopen | needs_more_evidence | 需要 Handoff Artifact spec + Evaluator rubric + executable proof-gate，当前多模型未认证 final。 |

## 建议你优先审批

### A. 建议 approve_reopen（高优先级）

1. T02 — P1 continuation / budget exhaustion resume
2. T04 — P1 continuous verification / pre-merge layer
3. T17 — P1 Karpathy negative-space evals

可选加严：
4. T08 — AgentMemory governance selfcheck，如果你要求 selfcheck 必须真实存在才算 done
5. T19 — 长任务管理治理，如果你要求 evaluator closure 必须真实落地才算 done

### B. 建议 approve_watch

1. T09 — source freshness matrix，仅作为治理/矩阵产物
2. T13 — wrong-source supersede atom，作为纠错/撤销记录

### C. 建议 approve_close_as_partial，不当作最终集成

T03, T10, T11, T12, T14, T15, T16

这些可以保留为阶段性学习成果，但后续若要采用，必须新建/重开 prototype/benchmark/adopt-update 任务。

### D. 建议先补证据，不立即审批最终关闭

T01, T05, T06, T07, T08, T18, T19

补证据类型：

- commit hash / changed files
- skill/script/config path
- pytest/selfcheck/proof-check output
- dashboard/report/read-back artifact
- 是否已进入 taskpool 后续阶段

## 多模型共同指出的系统问题

1. `truth_gate=no_claims` 不能代表任务复核通过。
2. `done` 任务如果只有 advisory/py_compile/hash/ExperienceAtom，不应自动视为最终集成。
3. P1/P2 且包含 not_certified/advisory/ratification-pending/prototype/candidate 的任务，默认应 reopen 或补证据。
4. 后续应给 taskpool/consult_models 增加 done-task evidence gate，防止空 claims 或阶段性证据被误判为 final landed。
