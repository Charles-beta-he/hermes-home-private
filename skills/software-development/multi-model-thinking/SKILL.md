---
name: multi-model-thinking
description: "真正多模型思考协议 — Claude Code + Codex/gpt-5.5 + DeepSeek + MiMo 独立方案、交叉质疑、来回讨论、补充红队、最终多方认证最佳方案。触发词: 多模型思考, 真多模型, 多模型讨论, 双脑, 四脑, multi-model thinking, debate, ratification"
license: MIT
---

# True Multi-Model Thinking Protocol — 真多模型思考协议

> 正确性 > 完整性 > 速度。先做对，再做全，最后做快。
>
> 旧版“两模型：主设计 → 第二模型验证 → 合并”只能算 cross-check，不算真正讨论。
> 真多模型必须满足：N>=3 独立模型、结构化交叉质疑、提案方回应/修订、补充红队、最终多方认证当前方案为约束内最佳。

## Evidence-First Rule (must apply during Phases 2-7)

Model agreement is not evidence. The main orchestrator owns tool execution and evidence collection; reviewer models own critique, evidence requests, and risk analysis.

When using `consult_models.py`:
- Put factual assertions in `state.claims` and tool outputs in `state.evidence`.
- Require each model to cite `evidence_bundle.grounding` for factual claims.
- If evidence is missing, the model must emit `evidence_requests` with the read-only command/query needed.
- Ratification cannot certify severity>=3 claims that are unsupported or contradicted, even if every model agrees.
- Do not enable SPL compression unless explicitly needed (`HERMES_MULTI_BRAIN_USE_SPL=1`); state compression must not hide claims/evidence.

This keeps the roles clean: orchestrator = tool/evidence brain; planners/reviewers = reasoning brains.

## 默认模型组合

默认使用 4 个互补模型：

- Claude Code / Claude: P10 架构、约束归一化、最终 synthesis；适合长上下文和复杂权衡。
- Codex / gpt-5.5: codegen/API/类型/工程落地审查；当前会话若是 Codex，可作为本方模型。
- DeepSeek: 独立低成本 reviewer / adversarial challenger；擅长逻辑漏洞和替代路线，但不要单独仲裁。
- MiMo-v2.5-pro: 低成本 sanity、实现成本/速度/简单性审查；适合快速发现明显问题和成本过高方案。

最小可接受：N=3 且 provider 至少 3 类。用户明确要求 Claude Code+Codex+DeepSeek+MiMo 时，必须 N=4，不得用 quorum=3 偷省一个模型。

## 标准流程：8 阶段，不可跳过核心讨论

```
Phase 0: Framing / State
  - 由主模型/编排器准备 state.json：明确 question、repo/context、constraints、acceptance criteria、non-goals、budget、risk level。
  - state.json 是事实输入和落地边界，不是候选方案；必须尽量客观、紧凑、可复现。
  - 主模型同时准备 implementation target / 落地方案骨架：目标文件、验收命令、风险边界、禁止改动项。
  - 计算 state_hash。所有模型看到同一份 state.json，避免上下文不一致。

Phase 1: Blind Seed Proposals
  - 4 个模型独立生成方案，禁止先看彼此答案，避免 anchoring。
  - 每份方案必须包含 assumptions、risks、implementation phases、cost controls、tests。

Phase 2: Normalize + Disagreement Ledger
  - 归一化为统一 schema。
  - 抽取 agreement / disagreement / missing evidence。
  - 建立 issue ledger：每个争议点有 id、severity、owner、status。

Phase 3: Cross-Critique / Challenge
  - 每个模型收到其他模型方案 + disagreement ledger。
  - 对每个其他方案输出 AGREE / AMEND / REJECT。
  - 质疑必须具体：引用原文/代码路径/成本数字/失败模式；必须给 correction 或 experiment。

Phase 4: Rebuttal + Revision
  - 每个模型必须逐条回应别人对自己的质疑：accept / reject-with-evidence / defer-to-risk。
  - 如接受质疑，输出 revision diff；如拒绝，必须给可验证理由。
  - 未回应的质疑不得进入“已认证”。

Phase 5: Supplementary Red-Team
  - 指定 devil's advocate 产出“当前最佳反例”。默认奇数轮 Codex，偶数轮 MiMo；高风险架构可让 DeepSeek 做逻辑红队。
  - 如果出现 novel severity>=3 critique，回到 Phase 3 聚焦该 issue。
  - 如果红队也只能 sign off，进入认证。

Phase 6: Convergence + Ratification
  - 每个模型独立投票：APPROVE / AMEND / REJECT。
  - 认证不是固定轮数，而是满足 stop condition。
  - 任何 severity=5 且未被技术性反驳的 dissent 都阻断认证。

Phase 7: Final Synthesis + Provenance
  - 合并最终方案，记录共识、分歧、采纳理由、未解决风险。
  - 输出可直接实施的 final_design.md / final_plan.json。
```

## 讨论循环

每轮讨论只围绕 unresolved issue ledger，避免全文反复发送：

```
round r:
  1. build_context = compact(problem_statement + current_best + unresolved_issues + prior_resolutions)
  2. challengers critique unresolved issues
  3. owners rebut or revise
  4. arbiter/judge 更新 issue status 和 agreement matrix
  5. red-team 尝试提出 novel blocker
  6. 若满足 stop_condition → ratify；否则继续下一轮
```

推荐上限：MAX_ROUNDS=5。上限只是防无限循环，不是认证条件。
如果达到上限仍有 blocker，输出 `not_certified`，不得谎称“最佳方案”。

## 停止条件：多方认证“当前最佳方案”

必须同时满足：

1. `approval_count >= N-1`，且 `reject_count == 0`。
2. agreement_matrix 在 problem framing、chosen approach、implementation order 三轴均 >= 0.85。
3. 本轮没有模型提交 revision diff。
4. Phase 5 没有 novel severity>=3 critique。
5. issue ledger 中没有 unresolved blocker；severity>=4 必须 resolved 或 explicitly accepted risk。
6. 每个模型都明确签署：`best_within_constraints=true`，并列出仍可能错的边界。
7. 没有 silent dissent：任何模型提出的质疑都必须收到 owner 回复。

硬上限触发时：
- 若只剩 severity<=2，可输出 certified_with_minor_risks。
- 若仍有 severity>=3 unresolved，输出 not_certified + escalation_needed，不执行实现。

## 质疑规则

禁止“你觉得呢”式泛问。每条 critique 使用结构化 schema：

```json
{
  "issue_id": "I-001",
  "target_model": "claude_code|codex|deepseek|mimo",
  "verdict": "agree|amend|reject",
  "severity": 1,
  "claim": "被质疑的具体主张",
  "evidence": "引用原文/代码路径/成本数字/失败模式",
  "reasoning": "为什么这是问题",
  "correction": "建议修正或替代方案",
  "experiment": "如何验证",
  "novel": true
}
```

规则：
- 每个模型必须给出最佳反方论点；如果无质疑，必须输出 signed_off=true 和为什么无法继续改进。
- 重复质疑无新证据时标记 duplicate，不延长循环。
- 质疑必须可行动：correction 或 experiment 至少一个非空。
- DeepSeek/MiMo 的少数意见不能因模型较便宜而直接忽略；按 severity 和 evidence 质量处理。
- Claude/Codex 也不能以权威身份压制其他模型；最终以 issue resolution 认证，不以模型名认证。

## 输出格式

最终输出必须包含：

```json
{
  "status": "certified|certified_with_minor_risks|not_certified",
  "models_consulted": ["claude_code", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"],
  "rounds_used": 3,
  "agreement_matrix": {"framing": 0.0, "approach": 0.0, "implementation_order": 0.0},
  "final_design": {},
  "issue_ledger": [
    {"id": "I-001", "status": "resolved|accepted_risk|unresolved", "severity": 3, "resolution": "..."}
  ],
  "ratification_votes": [
    {"model": "...", "vote": "approve|amend|reject", "best_within_constraints": true, "reasoning": "..."}
  ],
  "provenance": ["which model contributed which key insight"],
  "remaining_risks": []
}
```

## Dual-track anti-drift landing

当用户要求“长时自主开发防漂 / 双轨防漂 / estimator-controller 解耦 / Hermes 融合”时，不要只跑 LLM 互检。先把事实分层：

- Track A deterministic oracle：类型、测试、lint、scope contract、anchor lock、架构/视觉等机器可复现检查。Track A fail 一票否决，不能被多模型同意覆盖。
- Track B LLM critic：`consult_models.py --discussion`、DeepSeek/Codex/MiMo/Claude 互审、semantic drift/scope creep/anchor violation 语义嗅探。Track B fail 而 Track A pass 时默认 ask/escalate，而不是直接 block。
- Judge：合并 truth table；输出 JSON artifact，进入本地 brain/evidence index。

Hermes-native 起步脚本：

```bash
python3 ~/.hermes/scripts/anti_drift_guard.py --root /path/to/repo init --goal "immutable goal"
python3 ~/.hermes/scripts/anti_drift_guard.py --root /path/to/repo check-anchors
python3 ~/.hermes/scripts/anti_drift_guard.py --root /path/to/repo scope --contract .omc/state/tasks/TASK.contract.json
python3 ~/.hermes/scripts/anti_drift_guard.py --root /path/to/repo judge --track-a /tmp/track-a.json --track-b /tmp/track-b.json
python3 ~/.hermes/scripts/anti_drift_guard.py --root /path/to/repo consult-state --track-a /tmp/track-a.json --out /tmp/drift-review-state.json
```

核心约束：
- `.omc/anchors/.lock` 是不可变锚的 sha256 ledger；agent 修改 anchor 必须 halt/re-lock by explicit decision。
- task contract 用 JSON：`expected_files`、`allowed_globs`、`forbidden_files`、`forbidden_globs`、`loc_budget`。
- `consult-state` 只生成 evidence-first state；是否调用四脑由 orchestrator 决定，避免每次 edit 都烧多模型成本。
- Track A/Track B 的证据可以通过 `brainctl.py` 同步进 `~/Documents/brain`，SQLite index 只是可重建派生层。

## Hermes 当前落地方式

`consult_models.py` 已落地基础 DiscussionOrchestrator 能力：state builder、issue ledger、ratification gate、`--discussion` CLI、DeepSeek direct API fallback。

### 1. 主模型/编排器生成 state.json

```bash
python3 ~/.hermes/scripts/consult_models.py state \
  '你的问题/落地目标' \
  --context-json '{"repo":"/path/to/repo"}' \
  --constraint 'use four models' \
  --accept 'ratification gates pass' \
  --file consult_models.py \
  --verify 'python3 -m unittest ~/.hermes/scripts/test_consult_models_integration.py -v' \
  --out /tmp/mm-state.json
```

### 2. 四模型 fan-out + 讨论认证

```bash
python3 ~/.hermes/scripts/consult_models.py run /tmp/mm-state.json \
  --tier T3 \
  --quorum 4 \
  --discussion \
  --max-rounds 5 \
  --keep
```

### 3. 离线/测试模式

```bash
HERMES_MULTI_BRAIN_OFFLINE=1 python3 ~/.hermes/scripts/consult_models.py run /tmp/mm-state.json \
  --tier T3 --quorum 4 --shadow --discussion --max-rounds 2 --keep
```

输出 tick 目录中会包含：
- `plans/*.json`：各模型 seed proposal。
- `merged_plan.json`：consensus merge。
- `discussion_result.json`：status、issue_ledger、ratification_votes、agreement_matrix、remaining_risks。

注意：
- `~/.hermes/config/quorum.yaml` 的 T2/T3 虽列出 4 个 planners，但默认 quorum=3 会截断为 3 个模型；完整四模型必须 `--quorum 4`。
- Claude Code 需要完整能力时优先 `claude -p`；Hermes Anthropic adapter 是 fallback。
- Codex/gpt-5.5 走 openai-codex provider。
- MiMo 走 xiaomi provider。
- Hermes CLI 当前不接受 `--provider deepseek` 时，`consult_models.py` 对 `provider: deepseek` 使用 DeepSeek direct API fallback。
- 所有跨模型上下文必须 structured summary relay；不要假设 provider 共享上下文。
- Claude budget 是硬约束；预算不足时可降级，但必须在 final output 写明缺席模型，不能声称完整四模型认证。
- `delegate_task`/子代理审查可以作为补充 reviewer，但不是完整 `consult_models.py --discussion` 的替代品；如果任何 reviewer 超时、被截断或未完成，最终状态必须降级为 `certified_with_minor_risks` 或 `not_certified`，并在 provenance 中写明缺席/超时模型和由主编排器补充的证据。

## 何时使用

使用：
- 架构设计、新系统/模块、影响 >3 文件的关键决策。
- 高风险：安全、可靠性、成本、数据迁移、不可逆操作。
- 用户明确要求“多模型讨论 / 真多模型 / 四脑 / 来回讨论 / 多方认证”。

不用：
- 简单 bug fix、机械配置、低风险单文件改动。

## 经验教训

1. 两模型验证不是讨论；没有 rebuttal/revision 就不是 debate。
2. quorum 列出 4 个模型不等于实际调用 4 个；检查 quorum 截断。
3. 停止条件不是“跑够 2-3 轮”，而是多方认证 + 无新高严重质疑。
4. 强模型的结论也必须经 issue ledger 验证；模型名不是证据。
5. 为防 token 爆炸，后续轮只传 unresolved issues + compact current_best，不传全量历史。
6. 到达 MAX_ROUNDS 仍有 blocker 时必须 `not_certified`，不能为了结束而声称最佳。

## 关联 Skill

- multi-model-architecture: L0-L5 多模型基础设施、quorum、consult_models.py。
- p10-architecture-self-check: P10 架构自检。
- incremental-implementation: 增量实施策略。
- post-update-patch-healing: 升级后 patch 恢复。
