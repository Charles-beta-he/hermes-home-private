# Hermes Pipeline Common Pitfalls

Extracted from `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-pipeline/SKILL.md` on 2026-07-01T08:57:36.131647+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Common Pitfalls

- **hermes chat -q 比直接 API 调用慢** — 但获得完整 tool calling + skill 加载
- **Programmatic JSON 需要 quiet mode** — confirmer/validator 解析 JSON 时使用 `-Q`/`HERMES_NO_BANNER=1` 抑制 banner；不要使用未知 CLI 参数（例如旧版 `--toolsets none` 会输出 warning 并污染 JSON）。仍需用 robust extractor 从 mixed stdout 中取 JSON。
- **只保存真实 Hermes session id** — `--resume` 必须使用 Hermes 真实 session id；禁止按时间戳伪造 `arc-{project}-{ts}`。首轮用稳定 `--source` tag，之后从 stdout/stderr 或 `hermes sessions list --source <tag>` 提取真实 id，提取失败就不 resume。
- **Backpressure 要贯穿所有阶段** — pipeline 的 `--limit` 不应只限制 execute；confirm/execute/full 都要支持同一 limit，且 limit 只裁剪"需要新处理"的任务，不隐藏 already-confirmed/validated 的既有状态。
- **状态必须反映最终验证结果** — executor 可先临时写 DONE 以保存 output，但 build failure、auto-fix failure、browser harness critical issues 必须最终覆盖为 FAILED；避免通知失败/验证失败后留下假 DONE。
- **为边界状态写回归测试** — 覆盖 build result 缺少 `error` 但有 `output`、browser harness critical→FAILED、mixed Hermes JSON、真实 session id 提取、confirm limit 等容易在无人值守 loop 中变成 silent failure 的路径。
- **Git hygiene: pycache 可能已被跟踪** — 添加 `.gitignore` 不会停止跟踪已入库 `__pycache__/*.pyc`；用 `git ls-files '*__pycache__*' '*.pyc'` 检查，必要时 `git rm --cached` 或删除并 commit 清理，验证前后都看 `git status --short`。
- **SKIPPED vs FAILED** — 不可执行任务用 SKIPPED，保留重试能力，通过通知让用户知晓
- **错误隔离** — 每个步骤独立 try-catch，单个 envelope 失败不阻断其他
- **Python 3.9 兼容** — 加 `from __future__ import annotations`，用 `Optional[dict]` 或 `dict | None`（需 future annotations）
- **Comments API 404** — Lark 评论 API 可能需要额外权限，降级处理返回空列表
- **token 过期** — 自动刷新需要 LARK_APP_ID/LARK_APP_SECRET 环境变量
- **无限重试** — validator reject 必须加 retry_count + max_retries 限制
- **confirm 重复分析** — 过滤已有 confirm_plan 的任务，只分析新任务
- **共享代码** — 认证等重复逻辑提取到共享模块，不要 copy-paste
- **Claim-delegate 死锁** — controller 如果只 claim 不 delegate，任务会永远卡在 claimed 状态。正确做法是 claim 后立即 delegate（在同一 cycle 内），或者让 envelope_executor 消费 PENDING envelopes。executor 用 `hermes chat -q` 跑 worker 时如果太重（max_turns=60, 600s timeout），会超时导致 envelope 卡在 RUNNING。轻量化 worker: max_turns=15, MiMo 模型, 300s timeout。详见 multi-model-thinking skill 的 `references/task-flow-deadlock-detection-and-fix.md`。
- **brain_task_orchestrator list 输出用 `rows` 不是 `tasks`** — `list --json` 返回 `{"rows":[...]}` 不是 `{"tasks":[...]}`，读取时用 `data.get('rows', [])`。
- **hermes cron edit 不支持 --model** — 改 cron job 的 model/provider 用 `cronjob(action='update')` 工具，不是 `hermes cron edit`。修改后 last_error 仍是历史记录，下次运行才生效。
- **hermes kanban create 输出格式** — `Created t_xxxx (ready, assignee=xxx)`，提取 ID 用 `re.search(r'Created\s+(t_[a-f0-9]+)', output)`。
- **envelope bus + pipeline tick 详见** `references/envelope-bus-implementation.md`。
- **brain_task_orchestrator 集成模式详见** `references/brain-task-orchestrator-integration.md`。
- **envelope_executor 是 PENDING envelope 的消费者** — pipeline_tick 创建 envelope，executor 消费它们。详见 `references/envelope-executor-missing-link.md`。
- **envelope bus DB at `~/.hermes/state/envelope_bus.db`** — NOT `~/.hermes/scripts/envelope_state.db` (stale/empty). Escape ack at `~/.hermes/state/envelope_escape_ack.json`. Always query state/ for diagnostics.
- **Human escape diagnostic workflow** — when `stats` shows `human_escape_triggered: true`, query FAILED envelopes from state/ DB, identify failure pattern (missing_proof/invalid_proof/timeout/HTTP 429), report to user with ack/resume instructions. **Project-level clustering is the key signal:** if all post-ack failures are in one project with the same error, it's a systematic worker issue; fix before ACKing. If failures scatter across projects, it's likely infrastructure flakiness. See `references/envelope-executor-missing-link.md` § Diagnosing Human Escape and § Common Escape Causes.
- **Escape-triggered cron alert precedence** — when `pipeline_tick.py tick` returns `escape_triggered=true`, ALWAYS produce a prominent alert, even if `new_envelopes=0` and `timeouts_handled=0`. Escape is a safety-critical signal that overrides the silent-when-nothing-new rule. **Failure migration pattern**: after ACKing one failure class (e.g. HTTP 429), a different class (e.g. proof-gate, stale-running) can re-trigger escape within hours — this is the pipeline cleaning up to surface the next bottleneck, not a regression. See `references/escape-triggered-cron-alert-pattern.md` for the full diagnostic workflow, classification taxonomy, and report format.
- **Cron prompt pattern for escaped pipelines** — `"If status=escaped, ALERT."` triggers diagnostic report (stats + FAILED query + ack date + recommendation). Don't silently skip escaped state.
- **proof gate is the #1 failure mode** — workers complete but don't output valid PROOF_JSON. The worker prompt must include explicit proof output instructions. Fix at the source (worker prompt), not by relaxing the gate.
- **Never run long pipeline scripts synchronously** — scripts that delegate to `hermes chat -q` (envelope_executor, brain_task_orchestrator) can take 600s+ per envelope. The agent terminal times out at 60-300s. Always use `background=True, notify_on_complete=True` and poll for completion.
- **`timeout` CLI wrapper + executor SIGTERM handler = silent empty output** — the executor registers SIGTERM→kill worker group→SystemExit. Wrapping with `timeout 100 python3 envelope_executor.py run 1` triggers this handler on deadline, producing empty output with exit 0 (looks like success). Use the terminal tool's native timeout or `subprocess.run(timeout=N)` instead, which raises `TimeoutExpired` that the executor catches properly.
- **Cron script timeout (120s) vs worker timeout (600s) mismatch** — the cron system imposes a 120s script-level timeout on `no_agent` cron jobs, but `envelope_executor.py run N` spawns workers that take 300-600s each. The cron kills the executor mid-run, leaving RUNNING envelopes as orphans. After N cycles: N ghost RUNNING envelopes accumulate. Fix: increase cron timeout to ≥900s, or restructure as async (detach workers). Recovery: check appetite-aware stale detection (`started_at` + elapsed > `appetite_seconds`) before batch-resetting. See `references/cron-script-timeout-mismatch.md`.
- **Three consecutive timeouts = structural problem, not transient** — if the executor times out 3 times at different timeout values (120s, 300s, 120s), the worker timeout exceeds any reasonable cron window. Don't keep retrying; reset stale ghosts, report the mismatch, and suggest structural fixes (async workers or increased cron timeout).
- **完整自动触发链路** — orchestrator→pipeline_tick→envelope_executor→kanban_bridge，通过 cron 连接。pipeline-tick-hourly 创建，envelope-executor-cycle(30m) 消费，brain-kanban-bridge-sync(2h) 镜像，v-state-hourly 监控健康度。
1. Skipping prerequisite checks and assuming the environment already matches the workflow.
2. Applying the workflow mechanically without confirming that the request still matches this skill's trigger class.
3. Reporting success before reading back the actual outputs, files, or external side-effects.
