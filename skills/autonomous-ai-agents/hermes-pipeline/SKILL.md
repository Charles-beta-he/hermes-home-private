---
name: hermes-pipeline
description: Use when you need to build automated task pipelines using hermes chat -q as execution engine.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - pipeline
    - automation
    - hermes
    - orchestration
    - task-dispatch
    related_skills:
    - loop
    - multi-model-thinking
    - plan
    - requesting-code-review
    - router
    - software-development
    - harness-intake-contract
---

# Hermes Pipeline — Agent 执行引擎

## Overview


> 用 hermes chat -q 构建自动化任务流水线，skills 作为 pipeline 组件。

## When to Use

- 构建无人值守任务调度系统（Lark/Jira/GitHub Issues → 自动执行 → 结果写回）
- 需要多阶段验证的自动化流程（确认 → 执行 → 审查 → 报告）
- 用 hermes skills 作为 pipeline 组件（如 requesting-code-review 做 validator）

Don't use for:
- generic one-off scripting that does not need envelope/executor/validator orchestration;
- external dispatch, Lark mutation, scheduler/worker activation, or taskpool lifecycle writes without exact authority and readback;
- replacing deterministic proof with model agreement or pipeline status alone.

## Harness Intake Contract bridge

When a pipeline envelope, taskpool row, Lark task, social-video workflow lesson, or mission slice lacks enough structure for safe worker execution, load `harness-intake-contract` before confirmer/executor handoff. The confirmer should complete the map → goal → acceptance → division → evidence → gates contract, then derive executor and validator prompts from that contract. Missing acceptance or proof requirements should keep the item in intake/confirmation rather than letting a worker guess and later produce advisory-only `DONE`.

## 核心模式：Envelope Bus + Hermes Executor

```
任务源 → collector → confirmer(hermes) → executor(hermes) → validator(hermes) → reporter
                        ↓                    ↓                    ↓
                    SKIPPED+通知          DONE+output         pass/warn/reject
```

### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 执行引擎 | `hermes chat -q` | 完整 tool calling + skill 加载 + 多 provider |
| 确认模型 | hermes chat -q (Claude) | 准确性优先于成本 |
| 审查工具 | requesting-code-review skill | 复用已有 review pipeline |
| 状态存储 | SQLite envelope bus | 并发安全 + 查询能力 |
| 不可执行任务 | SKIPPED + 通知 | 非 FAILED，保留重试能力 |

## Implementation Pattern

### 1. Executor: hermes chat -q 替代直接 API 调用

```python
def execute_one(envelope):
    prompt = _build_prompt(envelope)
    cmd = [
        "hermes", "chat", "-q", prompt,
        "-s", "requesting-code-review",  # 加载 skill
        "--toolsets", "terminal,file",    # 只给需要的工具
    ]
    result = subprocess.run(cmd, cwd=project_path, timeout=600,
                            env={**os.environ, "HERMES_NO_BANNER": "1"})
    return result.stdout
```

### 2. Confirmer: 任务可行性分析

```python
def confirm(envelope):
    # hermes chat -q 做任务分析，输出 JSON
    raw = subprocess.run(["hermes", "chat", "-q", prompt, "--toolsets", "none"], ...)
    plan = extract_json(raw.stdout)

    if not plan["understood"]:
        # SKIPPED（非 FAILED）+ 发送通知
        db.update_status(eid, "SKIPPED")
        subprocess.run(["hermes", "chat", "-q", f"发送通知：{skip_reason}"], ...)
        return None
    return plan
```

### 3. Validator: 独立代码审查

```python
def validate(envelope):
    # 用 requesting-code-review skill 做 diff review
    verdict = subprocess.run([
        "hermes", "chat", "-q", review_prompt,
        "-s", "requesting-code-review",
    ], cwd=project_path, ...)

    if verdict == "reject":
        db.update_status(eid, "PENDING")  # 重置重试
```

### 4. Orchestrator: 错误隔离

```python
def run_full():
    for step in [collect, confirm, execute, validate, report]:
        try:
            step()
        except Exception as e:
            print(f"[{step.__name__} ERROR] {e}")
            # 不阻断后续步骤
```

## File Locations (Key Paths)

| Component | Path | Notes |
|-----------|------|-------|
| envelope_bus.py | `~/.hermes/scripts/envelope_bus.py` | Bus module (import) |
| envelope_executor.py | `~/.hermes/scripts/envelope_executor.py` | Executor CLI: `stats`, `run N`, `ack` |
| envelope_bus.db | `~/.hermes/state/envelope_bus.db` | **Actual SQLite state** |
| envelope_escape_ack.json | `~/.hermes/state/envelope_escape_ack.json` | Last human ack |
| task_continuation.py | `~/.hermes/scripts/task_continuation.py` | Budget exhaustion checkpoint |
| brain_task_orchestrator.py | `~/.hermes/scripts/brain_task_orchestrator.py` | Orchestrator CLI |

**⚠️ Common mistake**: `~/.hermes/scripts/envelope_state.db` exists but is stale/empty. The real DB is in `~/.hermes/state/`.

## Environment Variables

```
ARC_HERMES_CMD=hermes                    # hermes 命令路径
ARC_EXECUTOR_SKILLS=requesting-code-review  # executor 加载的 skills
ARC_EXECUTOR_TOOLSETS=terminal,file      # executor 工具集
ARC_EXECUTOR_TIMEOUT=600                 # executor 超时
ARC_VALIDATOR_TIMEOUT=120                # validator 超时
ARC_CONFIRM_TIMEOUT=60                   # confirmer 超时
LARK_APP_ID=cli_xxx                      # Lark App ID (token 刷新)
LARK_APP_SECRET=xxx                      # Lark App Secret (token 刷新)
```

## Envelope Data Model

```sql
CREATE TABLE envelopes (
    id          TEXT PRIMARY KEY,
    type        TEXT CHECK(type IN ('TASK','PLAN','RESULT','VALIDATION')),
    status      TEXT CHECK(status IN ('PENDING','RUNNING','DONE','FAILED','SKIPPED')),
    project     TEXT,              -- executor cwd
    payload     TEXT,              -- JSON: task + 各步骤产出
    trace       TEXT,              -- JSON array: 每步事件
    error       TEXT,
    created_at  TEXT,
    updated_at  TEXT
);
```

payload 关键字段:
```
lark_task_guid    任务 ID
summary           任务标题
description       详情
comments          评论区补充（文档链接等）
project_id        路由结果
confirm_plan      confirmer 输出
executor_output   executor 输出
validation        validator 结果
```

## Status Flow

```
PENDING → confirmer → PENDING (confirmed)
                    → SKIPPED (understood=false, 发送通知)
PENDING → executor → RUNNING → DONE
                              → FAILED (timeout/error)
DONE → validator → DONE (pass/warn)
                 → PENDING (reject, 重试)
DONE → reporter → DONE (已上报标记)
```

## Lark Token Auto-Refresh

```python
def _get_token():
    # 读取 token
    if expired:
        subprocess.run([
            "npx", "@larksuiteoapi/lark-mcp", "login",
            "--app-id", os.environ.get("LARK_APP_ID"),
            "--app-secret", os.environ.get("LARK_APP_SECRET"),
        ])
        # 重新读取
    return token
```

## Advanced Patterns (from arc-dispatch production)

Detailed `Advanced Patterns (from arc-dispatch production)` guidance moved to `references/advanced-patterns-from-arc-dispatch-production.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Unit Testing Pattern

Test each module with temporary SQLite:

```python
import tempfile
from pathlib import Path

def test_db_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        db.DB_PATH = Path(tmpdir) / "test.db"
        env = db.create(type="TASK", project="/tmp/test", payload={})
        assert db.get(env["id"])["status"] == "PENDING"

def test_confirm_skip():
    with tempfile.TemporaryDirectory() as tmpdir:
        db.DB_PATH = Path(tmpdir) / "test.db"
        env = db.create(type="TASK", project="/tmp/test",
                        payload={"confirm_plan": {"action": "fix"}})
        confirmed, skipped = confirmer.confirm_all(dry_run=True)
        assert len(confirmed) == 1  # pre-confirmed task included
```

Minimum test coverage: db CRUD, router matching, confirm skip, retry counter.

## Plan B/C/D Optimization Pattern

Three optimizations that reduce LLM calls and improve quality:

### Plan B: Skill Encapsulation

Create domain-specific skill for executor:

```markdown
# ~/.hermes/skills/software-development/my-executor/SKILL.md
## Steps: understand → locate → modify → verify → self-review → output verdict
## Definition of Done
```

Executor loads skill dynamically:
```python
skills = skill_map.get_skills_for_project(project_id)
cmd = [hermes, "chat", "-q", prompt, "-s", skills]
```

### Plan C: Self-Review in Executor (saves 1 LLM call/task)

Executor includes self-review and outputs JSON verdict:

```python
prompt = """
...task instructions...
## Self-review
1. Check git diff for security issues
2. Verify build passes
3. Output JSON verdict on LAST line:
   {"verdict": "pass|warn|reject", "summary": "...", "files_changed": [...]}
"""
```

Validator parses output instead of separate LLM call:
```python
verdict = _parse_verdict(executor_output)  # No hermes call needed
```

### Plan D: Session Persistence (reduce context re-injection)

Reuse hermes session across tasks in same project:

```python
SESSIONS_FILE = ~/.arc-dispatch/sessions.json  # {project_id: session_id}

existing_session = _get_session(project_id)
if existing_session:
    cmd = [hermes, "--resume", existing_session, "-q", prompt, ...]
else:
    cmd = [hermes, "chat", "-q", prompt, ...]
    # Save session ID after success
    _set_session(project_id, new_session_id)
```

## Hermes Feature Integration

### Memory — Cross-session project knowledge

```python
memory(action="add", target="memory", content="project uses Vue 2 + Vuex...")
```

Injected every turn. Executor doesn't re-read context.

### Gateway Notifications — Real-time updates

```python
notify.notify_task_completed(summary, project_id, files_changed)
notify.notify_task_failed(summary, project_id, error)
notify.notify_round_summary(db.count_by_status())
```

### Cron — Fully unattended

```bash
hermes cron create "*/30 * * * *" --name "pipeline" --prompt "run pipeline"
```

### Session Search — Reuse historical solutions

```python
similar = session_search.search_similar_tasks(f"{project_id} {task_summary}")
if similar:
    parts.append(f"## Historical Reference\n{similar[0]['content'][:300]}")
```

### Skill Map — Dynamic skill loading per project

```python
PROJECT_SKILLS = {
    "web_ui": "vue2-element-skill",
    "uaec_h5": "vue2-vant-skill",
    "partner_ui": "react-umi-skill",
}
skills = skill_map.get_skills_for_project(project_id)
```

### Delegate — Parallel execution

```python
delegate_task(tasks=[
    {goal: "execute web-ui task", context: "..."},
    {goal: "execute uaec-h5 task", context: "..."}
])
```

## Hybrid Execution Mode

Step-by-step with P10 audit between steps:

```
Step 1: Collect → report → user confirms
Step 2: Confirm → report → user confirms
Step 3: Execute --limit 1 → report → user confirms
Step 4: Validate → report → user confirms
Step 5: Report → done
```

Or fully automated via cron.

## Canonical Projection Cache for Mobile/Edge Sync

When a PWA/mobile/edge companion needs fast offline sync from Hermes-owned facts, keep the Gateway as a read-only projection boundary: Hermes SSOT (`state.db`/Brain) → exporter/writer → SQLite projection cache → Gateway ContextSource → client sync. Prefer background no-agent writers/watchers over request-path generation; success should be silent, failures should alert through the cron error path. The cache is not a second source of truth. Filter skill/system/planner/cron/iteration-relay/rich-writer noise before mobile sync. For LLM/Brain richer generation, use staging → source-bound validation → quality gate → backup promotion; for near-real-time updates, use session-end/idle watcher + incremental merge before promotion. See `references/canonical-projection-cache-pattern.md`.

## Full Auto-Trigger Chain (4-Model Certified 2026-05-11)

```
orchestrator.list (brain_task_orchestrator.py)
    ↓ cron: pipeline-tick-hourly
pipeline_tick.py (create PENDING envelopes from dispatchable tasks)
    ↓ cron: envelope-executor-cycle (every 30m)
envelope_executor.py (PENDING → claim → delegate to worker → DONE/BLOCKED/RETRY)
    ↓ cron: brain-kanban-bridge-sync (every 2h)
kanban_bridge.py (one-way mirror to Kanban for observability)
    ↓ cron: v-state-hourly
v_state.py (V(x) health score, alert if < 0.7)
```

Supporting crons:
- `agent-team-cycle-hourly` — dynamic N controller (claims tasks, conflict group scheduling)
- `orchestrator-selfcheck-6h` — brain_task_orchestrator.py selfcheck
- `memory-selfcheck-6h` — agent_memory_architecture_selfcheck.py

## V(x) State Function

System health score `V(x) = Σ wᵢ·fᵢ(xᵢ) ∈ [0,1]`. See `references/v-state-function.md`.

## Dynamic N + Task Classifier

Adaptive parallelism: `N = min(ceil(dispatchable/7), conflict_groups, 3)` with smoothing. See `references/dynamic-n-and-classifier.md`.

## Task Continuation (Budget Exhaustion Resume)

When worker hits "Iteration budget reached (60/60)", checkpoint progress and resume with injected context. Max 3 continuations. See `references/task-continuation-pattern.md`.

## Envelope Executor (The Missing Link)

Pipeline_tick creates PENDING envelopes but doesn't execute them. The executor consumes them. See `references/envelope-executor-missing-link.md`.

## Numeric Guardrails (4-Model Certified)

Detailed `Numeric Guardrails (4-Model Certified)` guidance moved to `references/numeric-guardrails-4-model-certified.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
## Self-Optimizing Verification Loop

When `verify_with_models` rejects a task, the system enters a self-improving loop:

1. `save_rejection()` — record rejection history
2. `analyze_rejection()` — detect patterns (missing_build/test/screenshot/evidence)
3. `generate_enhanced_criteria()` — expand acceptance 4→8 criteria
4. `update_project_profile()` — auto-learn rules into project profile
5. Retry with enhanced criteria (max 3 attempts)

Safety: no scope expansion, intent preservation, 3 failures → human escalation.

Full implementation: see multi-model-thinking skill `references/self-optimizing-verification-loop.md`.

## Capability Routing

Route tasks to appropriate models by type:

```python
needs_code = any(kw in title.lower() for kw in ['修复', 'fix', '实现', '代码', 'uvisa'])
model = 'gpt-5.5' if needs_code else 'mimo-v2.5-pro'
provider = 'openai-codex' if needs_code else 'xiaomi'
max_turns = 30 if needs_code else 15
timeout = 600 if needs_code else 300
```

## Common Pitfalls

Detailed Hermes Pipeline pitfalls moved to `references/common-pitfalls.md`.

Load it when envelope bus, executor, validator, projection cache, or auto-trigger chain behavior is failing.

Minimum in-root rule: pipeline status is not task completion; verify envelope state, executor receipt, output artifact, and lifecycle readback.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] The Definition of Done items above were explicitly checked, not assumed.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
