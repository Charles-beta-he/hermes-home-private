# Pitfalls (实战发现)

Extracted from `/Users/charles/.hermes/skills/software-development/self-improvement-pipeline/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Pitfalls (实战发现)

1. **Shell hook 仅在非 TTY 需要 auto_accept**: cron/gateway 环境需要提前设置 hooks_auto_accept: true, 否则 hook 静默不执行
2. **SQLite lastrowid 在 Python 3.12+ 行为不同**: `conn.execute().lastrowid` 报错. 改用 `cursor = conn.execute(...); cursor.fetchone()[0]`
3. **YAML frontmatter 中 description 含引号/冒号会解析失败**: 避免在 SKILL.md 的 frontmatter description 中使用双引号、单引号或冒号
4. **工具失败检测误报**: 工具返回 JSON 含 "error": null 作为 key name. 必须解析 JSON 后判断 exit_code 而非正则匹配 raw string
5. **hook 的 matcher 正则影响性能**: 匹配范围过大会每工具调用触发, 消耗 5ms/hook. 用具体 tool_name 限制
6. **ε-greedy 的 ε 不宜超过 10%**: 过高探索导致服务品质波动, 过低导致策略锁死

7. **Cron 全部静默不执行 → 先查 cron_mode 而非进程**:
   - `hermes cron status` 显示 "Gateway is not running — cron jobs will NOT fire"
   - 根因 99% 是 `approvals.cron_mode: deny` (默认值), 不是 scheduler 故障
   - 修复: `cron_mode: approve` + `hermes gateway install` (macOS launchd) + `hermes gateway status` 验证
   - `hermes cron tick` 会同步跑所有到期 job, 11 个 job 超 60s 超时 — 不要用它调试

8. **合成 trace 必须先打标再写入 — 否则污染 eval gate**:
   - 生成合成 trace 提升样本量 → pass_rate 虚高 → eval gate 放行回归 → 恶性循环
   - 正确流程: ALTER TABLE 加 `is_synthetic` → route_store.py 支持 `--synthetic` flag → summary 显示 Real/Synthetic 分拆
   - eval gate 必须用 `min_real_traces` (默认 20) 而非 total traces
   - Claude Code 在 2026-04-26 审计中直接指认为 P0 风险

9. **route_outcomes schema 迁移必须同步更新 4 处**:
   - (a) SQL ALTER TABLE 加列
   - (b) `_ensure_schema()` 的 CREATE TABLE IF NOT EXISTS (新安装用)
   - (c) `append()` 的 INSERT 语句
   - (d) CLI `--synthetic` flag + `append` 传参
   - 遗漏任一处 → 静默失败, 无报错

10. **Auto-approve 标准应写为 config 而非代码判断**:
    - config.yaml `evolve.auto_approve` section: criteria (eval_delta_min, canary_clean_hours, max_risk_level) + guard (require_p0_free, require_human 白名单)
    - 启用前置条件: real_traces≥50, canary 7d clean, dry-run 复现历史决策
    - 当前 enabled=false — 避免过早自动化

11. **`hermes chat -q` 不能用于 eval baseline 批量评估**:
    - 非 PTY 环境下返回 CLI 界面（Available Tools 列表）而非模型输出
    - subprocess 调用 120s 超时，且实际耗时 26-110s/prompt
    - 正确方案: 直接用 API（DeepSeek/Xiaomi/Anthropic）通过 `requests` 调用
    - `fill-baseline-parallel.py` 使用 ThreadPoolExecutor(max_workers=4) 并行填充
    - 85 prompts 约 2 分钟完成（vs hermes chat -q 串行 30+ 分钟）

12. **eval-harness init_baseline() 不能依赖虚构 skill 名**:
    - 旧版调用 `evaluate_skill("current_production")` → "Skill not found"
    - 正确实现: 直接遍历 prompts 列表，逐个调 API，结果写入 baseline
    - 已修复: `~/.hermes/scripts/eval-harness.py` 的 `init_baseline()` 函数

13. **Phase 6 consult-models nightly cron 必须显式注册，且必须 bounded-wrapper 化**:
    - multi-brain fan_out_merge 无内置调度，需 cron job 触发
    - Job: `multi-brain-consult-models-nightly`, schedule `0 1 * * *`
    - 旧命令 `python3 ~/.hermes/scripts/consult_models.py --keep --global` 已失效；新版 consult_models 需要 `state` → `run` 子命令
    - cron 中不要直接依赖长 prompt 或裸 `consult_models.py run`：T1 discussion/consensus 可能超时，导致 cron agent 空响应或 last_run_at 不刷新
    - 正确模式：创建 `~/.hermes/scripts/multi-brain-nightly-safe.py` 这类 wrapper，执行 `consult_models.py state` → bounded `consult_models.py run ... --tier T1 --quorum 3 --discussion --max-rounds 1 --keep` → 无论成功/timeout 都写 JSONL → 始终补跑 `usage-score.py`
    - wrapper 返回 0 并显式记录 `status=ok|timeout_recorded|degraded_recorded`，让 cron 健康不被静默空响应污染，同时保留审计证据

14. **Cron error/空响应治理优先 wrapper 化，不要只改 prompt**:
    - 症状: `hermes cron list` 中 job `last_status=error`，`last_delivery_error=null`，错误类似 "Agent completed but produced empty response"；或长任务 idle timeout 后没有可读产物。
    - 根因常见不是脚本坏，而是 prompt-only cron 让 LLM 负责执行/总结，长输出或超时后产生空回复；另一个常见根因是父脚本 timeout 后子进程仍占住 pipe，导致 wrapper 自己也被拖死。
    - 修复流程:
      1. `cronjob(action='list')` + `python3 ~/.hermes/scripts/cron-health-quarantine.py` 定位 bad jobs
      2. 先独立运行对应脚本，确认脚本能编译/执行: `python3 -m py_compile ...` + `python3 script.py`
      3. 对没有脚本的 prompt-only job，新增 `~/.hermes/scripts/<job>.py` wrapper，输出结构化 JSON/JSONL
      4. 长任务 wrapper 必须使用 `subprocess.Popen(..., start_new_session=True)`，`communicate(timeout=...)` 超时后 `os.killpg(proc.pid, signal.SIGTERM)`，必要时 SIGKILL；不要只用 `subprocess.run(timeout=...)`，否则 child process 可能继续占管道
      5. wrapper 应始终输出非空 JSON；对底层 partial failure 记录 `partial_fail_recorded`/`degraded_recorded`/`timeout_recorded` 并写 JSONL，wrapper 自身可 exit 0 让 cron 保留可总结产物
      6. 更新 cron 时优先使用**无参数 wrapper 脚本**，例如 `script='multi-model-smoke-hourly-wrapper.py'`，把参数写进 wrapper 内部；不要假设 `script='wrapper.py --flag value'` 会被 shell 拆分。已观察到 cron pre-run injector 会把 `multi-model-smoke-safe.py --timeout 210 ...` 当成单个文件路径并报 `Script not found`。
      7. 如果必须在 cron `script` 字段携带参数，先用 `cronjob(action='run')` 做一次验证，并检查 `~/.hermes/cron/output/<job_id>/...md` 是否出现 `Script not found: /path/script.py --arg`。出现则立即改回 no-arg wrapper。
      8. 对 script-first job，prompt 只做 2-3 行摘要；不要让 prompt 再运行 `p10-health.sh`、创建/删除 cron、或加载长 skill。否则脚本已成功但 LLM 摘要阶段仍可能 idle timeout。
      9. `cronjob(action='run')` 手动触发，等待 scheduler 消化后复查 `last_status`；不要把 `next_run_at` 变化误判为已执行完成
      10. 验证: wrapper 单测覆盖 timeout kill process tree、partial failure JSON、参数转发；`cron-health-quarantine.py` bad_count=0，`p10-health.sh --json` cron_bad=0 或 safe wrapper timeout_recorded 可审计，`usage-score.py` grade 保持 A
    - 对日频/周频 job 的 `last_run_at=null` 不要直接当故障；先看 `next_run_at` 是否尚未到首次触发窗口。

15. **自进化优先级队列要防幽灵信号，不要让旧基线永远排队**:
    - 症状: `self-improvement-pipeline.py --preview` 在 `usage-score.py` 已是 A、`cron_bad=0` 后仍输出 HIGH 工具失败；或 p10/p9/p7 已有 accepted 高分记录，却仍因旧 Darwin baseline 显示 `<60`。
    - 根因: priority 聚合读取历史 JSONL/TSV 时只聚合旧信号，不检查当前 operational health；Darwin `results.tsv` 可能有 8 列记录，解析器若要求 `len(cols) >= 9` 会跳过后续 accepted 修复行，只保留旧低分行。
    - 修复模式:
      1. 先跑当前事实: `python3 ~/.hermes/scripts/usage-score.py`, `python3 ~/.hermes/scripts/cron-health-quarantine.py`, `python3 ~/.hermes/scripts/self-improvement-pipeline.py --preview`
      2. 若 usage Grade A 且 cron `bad=0`，超过治理窗口的旧 `tool_failures` 信号应视为 stale transient，不再生成 HIGH priority；不要删除原始 audit log。超过 7 天的 tool failure 即使 usage 暂时不是 A 也应 suppress，因为真实问题会被新 autopsy 在 7d 窗口内重新发出。
      3. Darwin priority 必须按 skill 取**最新记录**，不能遍历所有历史低分；`results.tsv` 解析要兼容 8 列与 9 列。
      4. 给 `self-improvement-pipeline.py` 加回归测试: stale tool failure suppression + latest-score-per-skill。
      5. 把测试接入 `self-test.py`，让优先级队列 ghost 不再回归。
    - 验证目标: `self-improvement-pipeline.py --preview` 输出“无待办改进项”或只剩真实当前问题；`usage-score.py` Grade A；`cron-health-quarantine.py bad_count=0`；`self-test.py` 全绿。

16. **usage-score 不要把“24h 无非 hook 调用”误判成系统 D 级**:
    - 症状: self-test 59/59、route 7d pass≈96%、多模型 smoke 7d 有真实记录，但 `usage-score.py` 因 24h 只有 hook rows，model_breadth/real_call_integrity/route_diversity 全为 0，最终 Grade D。
    - 根因: 个人 Agent 的真实多模型调用是低频批任务，24h 窗口可能天然稀疏；hook rows 被正确排除后 denominator=0，不能等价为健康失败。
    - 修复模式:
      1. 24h 仍是主窗口；若非 hook call_rows < 10，则对 breadth/integrity/diversity 使用 7d fallback。
      2. fallback 分数必须 capped（建议 0.7×7d score），保留新鲜度压力，避免靠历史数据长期躺平。
      3. 输出中显式标注 `fallback_used`, `fallback_hours`, 以及 7d evaluated rows，避免把 fallback 当实时绿灯。
      4. p10-health 的 self-test 必须用 exit-code + bounded subprocess，不要 `grep -q ALL PASS` 管道；`set -euo pipefail` 下 grep -q 早退可能 SIGPIPE 上游，制造 false negative。
      5. 旧 cron `last_status=error` 如果是 >24h 的 transient wrapper/interpreter shutdown 且已有 future retry，可标记 stale 而非 live bad；真正清除仍要手动或定时重跑该 job。
    - 验证目标: `bash ~/.hermes/scripts/p10-health.sh --json` Grade A 且 warnings=[]；`python3 ~/.hermes/scripts/usage-score.py` Grade A/B（fallback_used 可审计）；`python3 ~/.hermes/scripts/cron-health-quarantine.py` bad_count=0；`python3 ~/.hermes/scripts/cron-missed-run-guard.py` missed_count=0。
17. **usage/self-improvement evidence readiness 修复要同时检查“证据存在”和“日志语义可被计分器识别”**:
    - 症状: 已有真实 multi-model/ensemble 调用，`usage-score.py` 仍输出 `semantic_grades.evidence_readiness.missing=['ensemble_executed']` 或 `ratification_corpus` 缺失。
    - 根因常见有两类：
      1. `consult_models.py` 已写 `tick-*/discussion_result.json`，但 usage-score 只读 `logs/ratify.jsonl` / `cross-patch.jsonl`，未把 certified discussion artifacts 视为 ratification corpus。
      2. `ensemble-vote.py --execute` 真实调用了模型，但日志没有持久化 `execute: true`，导致 usage-score 过滤条件不命中。
    - 修复模式：
      1. 对 certified `tick-*/discussion_result.json` 建一等 evidence reader：要求 `status in {certified, certified_with_minor_risks}`、truth gate 不为 `can_certify_truth=false`、2+ models participated、mtime 在 7d 窗口内；component 输出 `sources` 便于诊断来自 `discussion_result` 还是 jsonl bridge。
      2. `ensemble-vote.py` 的 executed path 必须在 result/log entry 中写 `execute: true`，并用回归测试 mock `_call_model()` 验证 log 文件实际落字段。
      3. 刷新真实 ensemble evidence 时可用最小 smoke，但要预期部分 provider 可能失败；只要 log schema 可计数，usage-score 应如实展示 `count_7d` 与 missing 状态。
    - 验证目标: `python3 ~/.hermes/scripts/usage-score.py` 输出 Grade A，`semantic_grades.evidence_readiness.missing=[]`，`components.ensemble_executed.count_7d>=1`，`components.ratification_corpus.sources` 非空。

18. **独立 code review 对治理脚本特别容易发现“计数语义”与“分类顺序”漏洞，必须按 fail-closed 修复后复审**:
    - 典型 blocker：`pending_review_count` 把同一 `fix_tool_config` diagnostic 同时按 executed action 与 diagnostic path 双计数；或 `_error_signature()` 先匹配 generic `not_found`，导致更具体的 `module_not_found` 分支不可达。
    - 修复模式：先加 failing regression test（例如 actionable `fix_tool_config` 只计 1 个 pending review；`ModuleNotFoundError: No module named ...` 分类为 `module_not_found`），再改最小逻辑，再重新跑目标 tests + self-test + 独立 reviewer。
    - commit 前顺序：显式 pathspec stage → `git diff --cached --check` → added-lines secret scan → independent reviewer JSON verdict → reviewer 如 fail 则修复+复审 → `[verified]` scoped local commit。

19. **Skill Graphs 2.0 应作为审计门，而不是先改运行时 loader**:
    - 症状: skill 数量增长后，related_skills 形成深链或循环；agent 运行时不稳定地跳过依赖。
    - 正确分层:
      - atom: 单一原语，0 skill 依赖；
      - molecule: 1-10 个 atom 的显式工作流；
      - compound: 驱动 molecules 的高级 playbook/orchestrator。
    - 落地模式:
      1. `python3 ~/.hermes/scripts/skill-steward.py --graph-check --json --warn-only` 生成 `skills/steward/skill-graph-report.json`
      2. 严格 gate 用 `--graph-check --json`，发现 cycle/excessive_depth/typed_violations exit 2
      3. 本轮只做审计和迁移建议，不直接清理旧 skill，不改 runtime loader
      4. self-test 必须含 valid fixture 与 invalid fixture，证明 fail-closed 行为
    - 验证目标: `self-test.py` 全绿；`skill-graph-audit.schema.json` parseable；steward full report 含 `audits.skill_graph`。

20. **Advisory-only multimodel PASS 要“消费弱触发”，但不能变成认证权威**:
    - 症状: taskpool multimodel 对弱触发（如 `P0_priority`/`closeout_ratification`/`architecture_target`/`accuracy_keyword`）跑出 advisory-only PASS 后，任务仍以 `not_certified` 反复进入队列，浪费模型预算并遮挡真正需要认证的任务。
    - 修复模式: advisory-only plan 若 gate 返回 `PASS + LOOP_DONE`，持久化为 `PASS_ADVISORY_ONLY` + `decision=continue_loop`，写 `multimodel_status: advisory_completed`、`multimodel_round_status: advisory_passed`、`multimodel_advisory_only: true`、`multimodel_certification_authority: false`。
    - 关键边界: 不写 `multimodel_ratification_artifact`，`task_multimodel_passed()` 仍必须为 false；只消费弱 advisory trigger，不得屏蔽 `stale_claim`、`p0_evolution_blast_radius`、`loop_non_convergence` 等强认证触发。
    - 回归测试: 构造 weak-only P1 evolution task，写入 `PASS_ADVISORY_ONLY` 后验证不再重复触发；再设置 `retry_count >= 2` 验证强触发仍恢复。
    - 详细 runbook: `references/advisory-only-multimodel-pass-consumption.md`。
- `pro` — PUA Pro 自进化追踪 (依赖 evolution.md)
- `darwin-skill` — 单个 skill 优化
- `skill-ecosystem-governance` — 生态治理
- `loop` — 迭代执行
