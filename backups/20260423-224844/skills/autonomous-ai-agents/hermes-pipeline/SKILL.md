---
name: hermes-pipeline
description: "Build automated task pipelines using hermes chat -q as execution engine. Compose hermes skills (confirmer, executor, validator) into multi-stage workflows with SQLite envelope bus, error isolation, and Lark/webhook integration."
license: MIT
tags: [pipeline, automation, hermes, orchestration, task-dispatch]
---

# Hermes Pipeline — Agent 执行引擎

> 用 hermes chat -q 构建自动化任务流水线，skills 作为 pipeline 组件。

## When to Use

- 构建无人值守任务调度系统（Lark/Jira/GitHub Issues → 自动执行 → 结果写回）
- 需要多阶段验证的自动化流程（确认 → 执行 → 审查 → 报告）
- 用 hermes skills 作为 pipeline 组件（如 requesting-code-review 做 validator）

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

### Retry with Exponential Backoff

```python
def retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=30.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator

@retry_with_backoff(max_attempts=3, base_delay=2.0)
def run_hermes():
    return subprocess.run(cmd, timeout=600)
```

### Validator Retry Counter (prevent infinite loops)

```python
def validate_and_handle(envelope, verdict):
    if verdict["verdict"] == "reject":
        retry_count = envelope["payload"].get("retry_count", 0)
        max_retries = 2

        if retry_count >= max_retries:
            db.update_status(eid, "FAILED", error=f"rejected after {max_retries} retries")
        else:
            new_payload = {**envelope["payload"], "retry_count": retry_count + 1}
            db.set_payload(eid, new_payload)
            db.update_status(eid, "PENDING")
```

### Confirm Skip Logic (don't re-analyze)

```python
def confirm_all():
    pending = db.list_pending(type="TASK")
    need_confirm = [e for e in pending if not e["payload"].get("confirm_plan")]
    already_confirmed = [e for e in pending if e["payload"].get("confirm_plan")]
    # Only analyze tasks without confirm_plan
    for env in need_confirm:
        confirm(env)
    return already_confirmed + newly_confirmed
```

### Shared Auth Module

Extract duplicate auth code (e.g., Lark token) into single module:

```python
# lark_auth.py — shared by collector and reporter
def get_token():
    token = read_from_store()
    if expired:
        refresh()
        token = read_from_store()
    return token

# collector.py / reporter.py
import lark_auth
def _get_token():
    return lark_auth.get_token()
```

### DB Query Helpers

```python
def list_by_status(status, type=None, limit=100):
    """List envelopes by status, optionally filtered by type."""
    ...

def count_by_status():
    """Count envelopes by status. Returns {status: count} dict."""
    ...
```

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

## Pitfalls

- **hermes chat -q 比直接 API 调用慢** — 但获得完整 tool calling + skill 加载
- **SKIPPED vs FAILED** — 不可执行任务用 SKIPPED，保留重试能力，通过通知让用户知晓
- **错误隔离** — 每个步骤独立 try-catch，单个 envelope 失败不阻断其他
- **Python 3.9 兼容** — 加 `from __future__ import annotations`，用 `Optional[dict]` 或 `dict | None`（需 future annotations）
- **Comments API 404** — Lark 评论 API 可能需要额外权限，降级处理返回空列表
- **token 过期** — 自动刷新需要 LARK_APP_ID/LARK_APP_SECRET 环境变量
- **无限重试** — validator reject 必须加 retry_count + max_retries 限制
- **confirm 重复分析** — 过滤已有 confirm_plan 的任务，只分析新任务
- **共享代码** — 认证等重复逻辑提取到共享模块，不要 copy-paste
