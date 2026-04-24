---
name: hermes-workflow-orchestrator
description: "用 Hermes Agent 构建自动化工作流 — Memory/Gateway/Cron/Session/Skills 集成模式。当需要构建 Lark→Hermes→执行→写回 类型的自动化 pipeline 时使用。"
license: MIT
tags: [hermes, workflow, automation, orchestrator, pipeline]
---

# Hermes Workflow Orchestrator

> Hermes 强在纵深持久性（记得你、学习你、随时可达）；Claude Code 强在横向代码能力（LSP/AST 感知、harness 安全层、IDE 集成深度）。两者互补多于竞争。

## When to Use

- 构建外部系统（Lark/Jira/Linear）→ Agent 执行 → 结果写回 的自动化 pipeline
- 需要跨会话记忆、定时执行、多平台通知的工作流
- 需要结合 Hermes 编排能力和 Claude Code 代码能力的场景

## 核心架构

```
外部系统（Lark/Jira/GitHub）
    ↓
Collector（拉取任务 + 去重）
    ↓
Confirmer（廉价 LLM 过滤不可执行任务）
    ↓
Executor（hermes chat -q 执行，加载 skills）
    ↓
Validator（审查结果）
    ↓
Reporter（写回外部系统）
    ↓
Orchestrator（串联 + 错误隔离 + 通知）
```

## Hermes 能力集成

### 1. Memory — 跨会话记忆

```python
# 记住项目细节，减少重复上下文注入
memory(action="add", target="memory", content="项目使用 Vue 2 + Vuex + Element UI")
```

效果: executor 不用每次都读缓存，memory 直接注入。

### 2. Gateway — 多平台通知

```python
# 通过 hermes messaging 推送通知
subprocess.run(["hermes", "chat", "-q", "发送通知：任务完成", "--toolsets", "messaging"])
```

效果: Telegram/Discord/Slack 实时推送任务状态。

### 3. Cron — 定时执行

```python
# 注册定时任务
cronjob(action="create", name="workflow", schedule="*/30 * * * *", prompt="执行工作流")
```

效果: 全自动，无需人工干预。

### 4. Session 持久 — 上下文复用

```python
# 同项目复用 session，减少重复上下文
if existing_session:
    cmd = ["hermes", "--resume", session_id, "-q", prompt]
else:
    cmd = ["hermes", "chat", "-q", prompt]
```

效果: 同项目任务共享上下文，不用每次都注入项目信息。

### 5. Session Search — 历史复用

```python
# 搜索历史对话复用方案
subprocess.run(["hermes", "chat", "-q", "搜索类似任务", "--toolsets", "session_search"])
```

效果: 相似任务直接复用历史方案。

### 6. Skills — 领域知识注入

```python
# 按任务类型加载不同 skill
skills = get_skills_for_project(project_id)  # "arc-dispatch-executor,requesting-code-review"
cmd = ["hermes", "chat", "-q", prompt, "-s", skills]
```

效果: 每个任务注入最精准的领域知识。

### 7. Delegate — 并行执行

```python
# 并行执行多条任务
delegate_task(tasks=[
    {"goal": "执行任务A", "context": "..."},
    {"goal": "执行任务B", "context": "..."}
])
```

效果: 多条任务同时执行。

## Hermes + Claude Code 互补

| 维度 | Hermes | Claude Code |
|------|--------|-------------|
| 记忆 | Memory（跨会话） | 无（每次新会话） |
| 可达 | Gateway（多平台） | CLI only |
| 调度 | Cron（定时） | 需外部触发 |
| 代码 | 基本改文件 | LSP/AST 深度感知 |
| 安全 | toolsets 控制 | sandbox 隔离 |
| 执行 | hermes chat -q | claude --print |

**最佳实践**: Hermes 做编排层（调度/记忆/通知），Claude Code 做执行层（改代码/跑测试）。

```python
# Hermes 编排 + Claude Code 执行
executor = {
    "engine": "hermes",  # 编排层
    "executor": "claude",  # 执行层（通过 skill 委派）
    "skills": ["arc-dispatch-executor"],  # 领域知识
}
```

## 关键模式

### Confirmer 模式

用廉价 LLM（如 qwen3-8b）过滤不可执行任务，避免浪费昂贵 LLM 额度。

```python
# 确认可行性（廉价）
plan = call_cheap_llm(task_summary, project_context)
if not plan["understood"]:
    mark_skipped(task)
    notify_user(task, plan["skip_reason"])
    continue

# 执行（昂贵）
result = call_expensive_llm(task, plan)
```

### 自审模式

Executor 执行完后自审，减少单独的 validator LLM 调用。

```python
# executor prompt 增加自审指令
prompt = """
...执行任务...
完成后自审：
- 无硬编码密钥
- 构建通过
- 修改范围正确
输出 JSON verdict: {"verdict": "pass|warn|reject", "summary": "..."}
"""

# validator 只解析 JSON，不再调 LLM
verdict = parse_json_verdict(executor_output)
```

### 重试模式

指数退避重试，防止网络抖动导致任务失败。

```python
@retry_with_backoff(max_attempts=3, base_delay=2.0)
def execute():
    return subprocess.run(cmd, timeout=600)
```

### 错误隔离

每个 envelope 独立处理，单个失败不影响其他任务。

```python
for env in pending:
    try:
        process(env)
    except Exception as e:
        log_error(env, e)
        continue  # 不阻断其他任务
```

## Implementation Steps

1. **Collector**: 拉取外部系统任务 + 去重（SQL O(1)）
2. **Router**: 关键词路由到目标项目
3. **Confirmer**: 廉价 LLM 分析可行性
4. **Executor**: hermes chat -q 执行 + session 持久 + 自审
5. **Validator**: 解析 executor 输出的 JSON verdict
6. **Reporter**: 写回外部系统
7. **Orchestrator**: 串联 + 错误隔离 + 通知 + cron

## Pitfalls

- **Token 过期**: 外部系统 token 需要自动刷新机制
- **JSON 解析**: LLM 输出可能包含额外内容，需要 robust 的 JSON 提取（从最后一行开始找）
- **无限重试**: validator reject 需要计数器限制最大重试次数
- **Schema 迁移**: SQLite 新增字段需要重建表（ALTER TABLE 不支持 CHECK 约束修改）
- **Session 复用**: hermes --resume 需要正确的 session_id 管理
- **SKIPPED vs FAILED**: 不可执行任务用 SKIPPED（可通知），执行失败用 FAILED

## Definition of Done

- [ ] **Outcome**: 完整 pipeline 可运行，任务从采集到写回全流程打通
- [ ] **Process**: Collector→Router→Confirmer→Executor→Validator→Reporter 各模块独立可测
- [ ] **Style**: 错误隔离、重试机制、通知机制、状态追踪完整
- [ ] **Efficiency**: Session 复用减少上下文注入、自审减少 LLM 调用、SQL 去重 O(1)
