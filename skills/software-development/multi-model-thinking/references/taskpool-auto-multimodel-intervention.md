# Taskpool Auto Multi-Model Intervention

Extracted from `/Users/charles/.hermes/skills/software-development/multi-model-thinking/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Taskpool 自动多模型介入 (2026-05-11)

本地大脑任务池已落地自动多模型介入 pipeline，无需手动触发"对 Hermes 说"。

### 架构

```
dispatch tick (每 N 分钟)
  ├── multimodel-intervention-dry-run  → 扫描任务池，计算触发队列
  ├── convergence stats               → total/passed/triggered/pass_rate
  └── multimodel-intervention-step    → (env var 门控)
      ├── build_state                 → consult_models.py state (120s)
      ├── run_discussion              → consult_models.py run --tier T3 --quorum 4 --discussion (closeout: ~15-20min)
      ├── ratification_gate           → 7 check fail-closed gate
      └── task_mutation               → 写入 multimodel_status 到 frontmatter

并行模式 (ThreadPoolExecutor):
  multimodel-intervention-parallel-step --max-workers 3
    ├── dry-run → 选择 top-N 不同边界任务
    ├── boundary 冲突检测（同边界只选一个）
    └── ThreadPoolExecutor(N)
        ├── worker 1: build→discussion→gate→mutate
        ├── worker 2: build→discussion→gate→mutate
        └── worker 3: build→discussion→gate→mutate
    └── 汇总 passed/failed/errors + convergence
```

### Tier 选择策略

| Tier | Models | Time/task | 适用场景 |
|------|--------|-----------|----------|
| T0 | mimo only | ~1min | 简单 sanity check |
| T1 | gpt + deepseek | ~3min | 低风险 review |
| T2 | gpt + deepseek + mimo | ~8min | Advisory/routing only; not valid for final taskpool/Lark closeout |
| T3 | claude + gpt + deepseek + mimo | ~15-20min | Required for high-score taskpool closeout, architecture decisions, safety-critical |

任务池 advisory/routing 可以用 T2（3 模型，~8min），但 PUA-loop closeout / Lark done / 高分任务最终认证必须用 T3（4 模型，~15-20min）并通过 ratification-gate。

### 触发策略 (结构性优先 + 关键词补充)

- 强结构: P0+evolution / retry>=2 / stale_claim → 直接触发
- 弱结构: running/review / P0 / evolution / architecture_target → 需 >=2 信号
- 关键词: 仅搜索 title+concepts，需已有结构信号才补充
- 关键词精度: 移除 >50% 命中率噪音词 (evidence/truth/local-brain/skill 等)
- 当前触发率: 32% (18/56 tasks)

### 关键命令

```bash
# 扫描 + 收敛统计
python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-dry-run --json

# 串行执行一步 (需 env var)
HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-step --json

# 并行执行 (3 路并发，推荐)
HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-parallel-step --max-workers 3 --json

# ratification gate (双形态: Shape A 显式 criteria / Shape B 推导)
python3 ~/.hermes/scripts/brain_task_orchestrator.py ratification-gate --task TASK --discussion-result /path/to/discussion_result.json --json
```

### Gate 双形态

Shape A (显式): `criteria_satisfied.{accuracy, long_term_goal, one_shot_landing}` + `final_design.{next_slice, acceptance_evidence, rollback_boundary}`

Shape B (推导): `evidence_bundle.grounding` 全 verified → accuracy; `fanout_certification.multi_model_certified` → long_term_goal; `verification.guard_metrics` + `rollback_signal.auto_rollback_if` → one_shot_landing

Gate 模型数策略: taskpool automatic advisory/routing tiers may use tier-specific expected sets only when the state explicitly records that tier and the result is not being used for final Lark/done closeout. For closeout/certification under this user's policy, require the canonical 4-model set and fail 3/4 as `not_certified`. Never let self-attested `models_consulted` silently lower the closeout requirement.

### 自运行配置清单

开启自运行需要 3 个文件 + 2 个 env var:

```bash
# 1. env vars (持久化到 .zshrc)
export HERMES_LOCAL_BRAIN_AUTORUN=1
export HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1

# 2. autorun allowlist
~/.hermes/state/auto_run_allowlist.json  # ["project:xxx", "project:yyy"]

# 3. multimodel allowlist (可选，空=全部通过)
~/.hermes/state/multimodel_intervention_allowlist.json

# 4. autonomy-write-allowlist (必须，否则 auto-claim FAIL_CLOSED)
~/.hermes/config/autonomy-write-allowlist.json  # ["taskpool", "kanban-worker"]
```

### Cron

- job: `multimodel-intervention-step` (every 60m)
- 命令: `multimodel-intervention-parallel-step --max-workers 3 --json`
- job_id: `1883fd365c15`

### 新命令

```bash
# 并行 step（推荐，3 路并行，~48min 处理 18 任务）
HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-parallel-step --max-workers 3 --json

# 串行 step（单任务，调试用）
HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-step --json
```

### Pitfalls

1. discussion timeout: T3(4模型×5轮)需 1200s; T2(3模型×3轮)需 ~600s
2. state_path 清理: 防止 stale 目录导致 IsADirectoryError (shutil.rmtree)
3. shell=True: build/run 命令含 && 链，需 shell 执行
4. tick SKIP: allowed_statuses 必须含 SKIP，否则未激活 step 报 ERROR
5. scheduled-cron env gate: `multimodel-intervention-parallel-step` still requires `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1`. If the exact user/cron command omits it, the command returns `SKIP: autorun_multimodel_disabled` (exit 2). In an autonomous cron run where the intent is clearly to process tasks, rerun inline with `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 ...`, then report both the initial SKIP and the effective run result rather than claiming no work. For durable cron activation, prefer a no-argument wrapper script (for example `multimodel_intervention_parallel_step.py`) that sets the env var and calls `brain_task_orchestrator.py multimodel-intervention-parallel-step --max-workers 3 --json`; cron script fields do not source `.zshrc` and should not rely on embedded argv.
6. mimo-v2.5-pro: provider=xiaomi，最后执行，retry status 常见
6. build_state 缺 claims: 无 --claim 时 truth_status=no_claims → gate 必然 FAIL
7. errors 变量顺序: tick 中 errors=[] 必须在引用前初始化
8. 并行 tick 匹配: 多个 discussion 并发时需 task_id[:40] 模糊匹配 + 10min 时间窗
9. autonomy-write-allowlist: 缺此文件导致 auto-claim FAIL_CLOSED
10. gate 模型数策略: advisory/routing tiers may be tier-specific, but final Lark/taskpool closeout for this user requires the canonical four-model set. Do not lower requirements from `models_consulted`; 3/4 is `not_certified` for closeout.
11. dispatch safe-summary 双门控: cron/safe tick 不得因继承 `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1` 自动启动昂贵多模型 step。昂贵 step 必须同时满足显式 `--multimodel-step` 和 env gate；缺任一项返回 structured `SKIP`。超时必须 kill 整个 process group 并输出 parseable JSON；命令 ratchet 用 `shlex` 精确检查 `--tier T3`/`--quorum 4`，禁止 substring spoofing (`T30`/`40`)。详见 `references/taskpool-dispatch-tick-multimodel-ratchet.md`。
12. taskpool 派生视图必须在 canonical task-note 突变后同进程刷新: `add`、`ingest-inbox --write`、`claim`、`release`、`transition`、`retry`、`done`、`reconcile --write`、`permission-migrate --apply` 等写入 Markdown 后，应立即重建 dashboard / sorted pool / control center，并在 JSON 返回中暴露 `derived_refresh`。不要只依赖下一次 cron/dashboard 手动刷新，否则任务池流转和 human/cron control loop 会看到 stale state。
13. PUA-loop 多模型 step 必须“每轮写回”，不只 PASS 写回: PASS/LOOP_DONE 才写 `multimodel_ratification_artifact`；FAIL/SKIP/no_discussion_result 也要写 `multimodel_status: not_certified`、`multimodel_round_status`、`multimodel_last_gate_status`、`multimodel_last_decision`、`multimodel_last_discussion_artifact/state_path`、`multimodel_last_failures`，并刷新派生视图。这样下一轮 loop 能 fail-closed 继续，而不是静默无状态。注意 `certification_status` 是 mission-envelope 语义，不能写入普通任务或作为普通任务认证状态；普通任务多模型写回应使用 `multimodel_status`，并清理遗留 `certification_status`，否则 selfcheck/lifecycle/proof 可能把普通任务误判为缺字段的 mission envelope。PASS 判定必须先规范化 gate status/decision（如 lowercase `pass`/`loop_done`），再判断是否通过；非 PASS 必须清除 stale `multimodel_ratification_artifact`，dashboard 对非 passed 最新轮显示 latest discussion artifact，不显示旧 PASS artifact。
14. autorun/任务池测试夹具要同时 allowlist `taskpool` 和 `kanban-worker`: `auto-claim-and-handoff` 的 mutation surface 是 `taskpool`，只写 `kanban-worker` 会导致 `surface_allowlisted` FAIL_CLOSED。测试或临时环境设置 `HERMES_AUTONOMY_WRITE_ALLOWLIST` 时用 `["taskpool", "kanban-worker"]`，除非测试目标正是验证 taskpool allowlist 缺失。
