---
name: multi-model-thinking
description: Use when a task needs true multi-model deliberation, cross-critique, evidence-linked ratification, or high-risk final certification rather than a single-model answer or a simple cross-check.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - multi-model
    - ratification
    - evidence-first
    - certification
    - debate
    related_skills:
    - framework-audit
    - requesting-code-review
    - self-improvement-pipeline
---

# True Multi-Model Thinking Protocol — 真多模型思考协议

## Overview


> 正确性 > 完整性 > 速度。先做对，再做全，最后做快。
>
> 旧版“两模型：主设计 → 第二模型验证 → 合并”只能算 cross-check，不算真正讨论。
> 真多模型必须满足：N>=3 独立模型、结构化交叉质疑、提案方回应/修订、补充红队、最终多方认证当前方案为约束内最佳。

## Evidence-First Rule (must apply during Phases 2-7)

The detailed evidence-first ratification and linked-evidence rules were moved to `references/evidence-first-rule.md`.

Load it before packaging claims/evidence for `consult_models.py`, repository audits, code closeout, product/PRD certification, provider fallback, or taskpool ratification.

Minimum in-root rule: model agreement is not evidence; every severity>=3 claim needs explicit tool/file/command evidence linked to the claim ID.

## Provider-Specific Ratification Pitfalls

When running 4-model concurrent ratification, four provider-specific issues can block certification:

1. **MiMo returns empty content when called concurrently** — Xiaomi's API drops responses when hit simultaneously with other providers. Must run MiMo sequentially AFTER the concurrent trio (Claude+GPT+DeepSeek). Retry 3x with exponential backoff if still empty.

2. **DeepSeek reasoning tokens consume max_tokens budget** — `deepseek-v4-pro` emits chain-of-thought in `reasoning_content` which counts against `max_tokens`. With `max_tokens=500`, reasoning eats 2000+ chars and actual content truncates to ~50 chars with `finish_reason: length`. Need `max_tokens>=2000` for ratification prompts.

2a. **MiMo can also burn tiny `max_tokens` on reasoning and return empty content** — direct Xiaomi smoke with `max_tokens=16` can return HTTP 200, `completion_tokens=16`, `reasoning_tokens=15`, `finish_reason=stop`, but `message.content=""`. This is not quota exhaustion and not model approval. For smoke use `max_tokens>=64`; for ratification use a large budget (e.g. `>=1600`) and require non-empty parseable content.

3. **MiMo wraps JSON in ```json blocks** — The `extract_json()` function must handle markdown code block wrapping. Regex: `re.search(r'```(?:json)?\\\\s*(\\\\{.*?\\\\})\\\\s*```', s, re.S)`. Always fall through to `{`/`}` boundary extraction as last resort.

4. **Claude Code has two distinct paths** — for Claude Max/OAuth local nodes, `claude -p ... --output-format json` is the authoritative runtime. Do **not** use `hermes chat --provider anthropic` or `hermes chat --provider claude-code` as a health/certification probe: those paths can hit Anthropic-compatible adapter quota errors while the Claude Code CLI node is healthy. If `claude -p` hits `error_max_turns` on complex structured ratification, simplify the Claude prompt / allow more turns for that CLI call; do not fall back to the Hermes Anthropic adapter as proof of Claude participation.

4. **GPT-5.5 via openai-codex prefixes output** — May output `⚠️ Reached maximum iterations (1). Requesting summary...` before JSON. The `extract_json()` function must handle text before the JSON object via `s.find('{')` / `s.rfind('}')`.

Recommended 4-model ratification sequence:
```python
# Phase 1: concurrent trio
with ThreadPoolExecutor(max_workers=3) as ex:
    futs = {ex.submit(fn): model for model, fn in [
        ('claude', call_claude), ('gpt', call_gpt), ('deepseek', call_deepseek)
    ]}
    for fut in as_completed(futs):
        # collect results

# Phase 2: MiMo sequential (with 3x retry)
parsed = extract_json(call_mimo_with_retry())
```

Robust `extract_json()`:
```python
def extract_json(s):
    s = (s or '').strip()
    if not s: raise ValueError('empty response')
    try: return json.loads(s)
    except Exception: pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', s, re.S)
    if m: return json.loads(m.group(1))
    a = s.find('{'); b = s.rfind('}')
    if a >= 0 and b > a: return json.loads(s[a:b+1])
    raise ValueError(f'no json object ({len(s)} chars): {s[:200]}')
```

Full details, detection signals, and code patterns: `references/provider-concurrency-and-token-budget-pitfalls.md`.

## 默认模型组合

默认使用 4 个互补模型：

- Claude Code / Claude: P10 架构、约束归一化、最终 synthesis；适合长上下文和复杂权衡。
- Codex / gpt-5.5: codegen/API/类型/工程落地审查；当前会话若是 Codex，可作为本方模型。
- DeepSeek: 独立低成本 reviewer / adversarial challenger；擅长逻辑漏洞和替代路线，但不要单独仲裁。
- MiMo-v2.5-pro: 低成本 sanity、实现成本/速度/简单性审查；适合快速发现明显问题和成本过高方案。

最小可接受：N=3 且 provider 至少 3 类。用户明确要求 Claude Code+Codex+DeepSeek+MiMo 时，必须 N=4，不得用 quorum=3 偷省一个模型。

执行器并发限制不是降级理由：如果 `delegate_task` 或本地配置最多同时跑 3 个 child/reviewer，就拆成 `3 + 1` 两批执行，并在最终状态里合并 4 票。不要因为 `max_concurrent_children=3` 就把 4/4 认证降成 3/4；缺任一模型时只能标 `not_fully_certified` / advisory。

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

## Communication Budget Protocol — 防 token 内耗通信协议

`consult_models.py` 的 discussion round 默认使用 `multi_model_comm_packet_v1`，不要把 `merged_plan`、完整 `evidence_bundle`、完整 transcript 每轮广播给每个模型。

通信规则：
- 首轮 planner 可读取 state；后续 discussion 只收 `manifest_delta` packet。
- `artifact_manifest` 只传 full artifact 的 hash/char/token 统计，不传完整正文。
- `current_best_summary` 只传 patch id、target_file、op、risk、短 rationale、source_hash。
- `round_delta` 只传当前 unresolved issues、上轮 vote 摘要，不传长 reasoning 历史。
- `evidence_summary` 只传 claim/evidence count、grounding status、evidence ids；缺正文时 reviewer 必须输出 `evidence_requests`。
- 每轮 artifact 必须记录 `communication.estimated_chars_saved` / `estimated_tokens_saved`，让 token 成本可审计。
- 只有当 evidence_request 命中并由 orchestrator 执行后，才把新增 evidence 回填下一轮；禁止模型互相转述大段原文。

口令：模型之间传“索引卡 + 差异”，不传“全量小说”。

详细落地规范、telemetry 真实性规则、测试清单见 `references/communication-budget-protocol.md`。

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
- 当把本协议落到本地大脑时，必须有独立可检索的原则卡覆盖“少数意见 / 模型名不等于权威”。推荐 atom 标题包含“少数意见：模型名不是证据，模型名不等于权威”，避免搜索只命中任务日志而不命中原则本体。

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

## References

- `references/current-code-certification-after-amend.md` — post-ratification amendments or AMEND/not_certified current-code runs invalidate certification claims until blockers are converted into deterministic evidence and a fresh target-bound `discussion_result.json` plus `final/certification_manifest.json` pass with the exact 4-model set.
- `references/grounded-not-certified-amend-loop.md` — when truth evidence is grounded but T3 ratification is `not_certified`, inspect issue ledger/manifest, convert severity>=3 AMENDs into deterministic tests/evidence, commit, update state to current commits, and rerun fresh T3.
- `references/taskpool-artifact-verification-regression.md` — taskpool pass-state hardening: frontmatter `multimodel_status: certified` is only a hint; load the local `discussion_result.json`, bind it to the exact task, require canonical 4/4 votes for closeout, and repair stale/mismatched task notes to `not_certified` with proof-log caveats.
- `references/taskpool-multimodel-autorun-pitfalls.md` — **12 大 pitfalls**: build_state claims 注入、tick errors 初始化顺序、autonomy-write-allowlist、state_path 清理、1200s timeout、关键词误报爆炸、gate 双形态、convergence 统计解读、allowlist 配置、safe summary 双门控、evidence-spine auto-completer 语义分类、parallel consult tick 秒级目录碰撞/target-binding 污染治理。
- `references/taskpool-dispatch-tick-multimodel-ratchet.md` — safe-summary dispatch tick ratchet: expensive multimodel work requires explicit `--multimodel-step` plus env gate, timeout cleanup kills the whole process group, timeout output stays structured JSON, and static command checks use exact `shlex` flag parsing.
- `references/theory-impact-propagation.md` — theory-to-impact propagation: after a single slice is optimized under a theory/principle, bind a Theory Point ID, scan same-theory targets, build a Layer Impact Map across L0-L5/LX/skills/cron, add smoothing gates, and run `architecture_theory_impact_ratchet.py` so local patches do not become unsynchronized global rules.
- `references/taskpool-autonomy-readiness-and-evidence-spine.md` — taskpool autonomy readiness certification pattern: evidence-spine heartbeat, autonomy-readiness artifact, exact claim-linked T3 evidence, hollow-shell ratification selftests, proof-audit false-positive handling, timeout handoff, and 4/4 certification closeout discipline.
- `references/taskpool-boundary-coverage-permission-gates.md` — taskpool all-boundary coverage review pattern: run the read-only status/permission/cron/multimodel suite, distinguish core safety from all-boundary certification, classify Lark/work vs self-evolution completion gates, and treat `--yolo` as highest execution authority but never as done authority.
- `kanban-orchestrator:references/local-taskpool-system-repair.md` — system-repair pattern after taskpool status checks: fix deterministic proof/selfcheck/evidence/envelope gates first, then run a fresh current-state T3 certification; a grounded-but-not-certified planning tick can be used as advisory provenance but not as final certification.
- `references/long-term-taskpool-autorun-activation.md` — runbook for starting long-term local-brain taskpool autorun: prerequisite gates, no-arg cron wrappers, safe/autorun heartbeats, env-gated multimodel wrapper, cron proof, fail-closed `policy_missing`, closeout evidence, and rollback.
- `references/taskpool-pua-loop-hardening.md` — closeout pattern for PUA-loop/taskpool autonomy hardening: evidence-spine gate_status enforcement, cron secret redaction, malformed ratification artifact fail-closed tests, real-vault mission envelope repair, and scoped commit discipline.
- `references/provider-adapter-fallback-ratification.md` — consult_models.py adapter fallback
- `references/claude-code-wrapper-runtime-errors.md` — Claude Code `--output-format json` wrapper decoding: classify `is_error` / `api_error_status` runtime failures separately from malformed model JSON, with regression tests for planner/discussion paths.
- `references/direct-multi-model-ratification.md` — **Direct API ratification loop** with provider quirks: DeepSeek needs max_tokens>=2000, MiMo must be sequential (concurrent=empty), MiMo wraps JSON in code blocks. The 3+1 concurrent+sequential pattern, amend loops, certification levels.
- `references/vx-state-function-and-auto-trigger-chain.md` — **V(x) Lyapunov health function** from Complex Giant Systems theory, full auto-trigger chain (orchestrator→pipeline_tick→envelope_executor→kanban_bridge), PUA-loop + multi-model verification pattern, coverage audit methodology.
- `references/task-flow-deadlock-detection-and-fix.md` — **Task flow deadlock**: controller claims but never delegates, stale claims block dispatch. Detection via stale_claim field, fix via force-release + delegate_to_worker in controller.
- `references/iron-plate-consolidation-pattern.md` — **Iron plate consolidation**: 5-layer architecture (ops/health/evolve/watchdog/report) to merge 20+ cron jobs. GenericAgent patterns: 5-layer memory, task→SOP crystallization, file IPC sub-agents.

## Hermes 当前落地方式

The detailed Hermes current multi-model implementation and command notes were moved to `references/hermes-current-landing.md`.

Load it when operating or debugging the local taskpool multimodel intervention scripts, allowlists, routing gate, or ratification commands.

Minimum in-root rule: use deterministic evidence first, then multimodel review for unresolved risk/certification; do not turn advisory consensus into certified completion.

## When to Use
使用：
- 架构设计、新系统/模块、影响 >3 文件的关键决策。
- 高风险：安全、可靠性、成本、数据迁移、不可逆操作。
- 第三方 agent/orchestration 框架评估需要多视角时：至少拆成 architecture、security/supply-chain、product/workflow 三个独立 reviewer；固定 commit 和证据文件；最终 synthesis 必须区分"可借鉴治理原语"和"不应整体引入/需沙箱"的风险。
- 用户明确要求"多模型讨论 / 真多模型 / 四脑 / 来回讨论 / 多方认证"。
- 用户问"为什么你没发现这个"或要求分析架构盲点的根因 — 使用 `references/multi-model-root-cause-analysis.md` 的 6 理论框架诊断模式。

Don't use for:
- 简单 bug fix、机械配置、低风险单文件改动；
- evidence-clear local fixes where deterministic source/docs/tests already identify the smallest safe patch;
- replacing tool/file/command evidence with model agreement or advisory consensus.

## Cross-Cutting Concern Recognition (交叉关注点识别)

Detailed cross-cutting concern recognition notes were moved to `references/cross-cutting-concern-recognition.md`.

Load it when a point fix may actually represent shared infrastructure, validation, security, i18n, logging, or data-transform policy.

Minimum in-root rule: classify point-fix vs cross-cutting before editing; shared concerns should land as shared infrastructure plus tests.

## 经验教训

Detailed multi-model lessons learned were moved to `references/lessons-learned.md`.

Load it when previous provider/routing/certification pitfalls look relevant to the current task.

Minimum in-root rule: route by complexity, uncertainty, reflexivity, and blast radius; avoid multi-brain ceremony for evidence-clear local fixes.

## Taskpool 自动多模型介入 (2026-05-11)

Detailed taskpool automatic multi-model intervention commands and setup notes were moved to `references/taskpool-auto-multimodel-intervention.md`.

Load it when operating taskpool multimodel scan/step/allowlist/ratification commands.

Minimum in-root rule: automatic multimodel is evidence advisory until the exact task's proof and ratification gates pass; do not force lifecycle states.

## 关联 Skill

- multi-model-architecture: L0-L5 多模型基础设施、quorum、consult_models.py。
- p10-architecture-self-check: P10 架构自检。
- incremental-implementation: 增量实施策略。
- post-update-patch-healing: 升级后 patch 恢复。

## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
