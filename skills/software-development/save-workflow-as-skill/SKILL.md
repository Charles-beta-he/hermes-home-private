---
name: save-workflow-as-skill
description: "将刚完成的复杂任务流程保存为可复用的 skill。每次成功完成复杂任务后都应考虑。"
license: MIT
tags: [skill, save, workflow, reuse]
---

# Save Workflow as Skill

> 让刚学会的操作变成可复用的能力

## When to Use

- 完成了一个复杂任务（5+ 工具调用，涉及多个步骤）
- 发现了一个重复性工作模式
- 修复了一个需要额外上下文的 bug
- 配置了一个需要记住参数的脚本

## Process

### Step 1: 确认值得保存

| 判断条件 | ✅ 保存 | ❌ 跳过 |
|---------|--------|--------|
| 步骤数 | > 5 步 | 1-3 步 |
| 复用概率 | 每周至少一次 | 一次性任务 |
| 操作复杂度 | 容易忘的参数/顺序 | CLI --help 就够 |

### Step 2: 创建 skill

```bash
# 用 skill_manage 创建
skill_manage(
    action="create",
    name="my-workflow-name",
    content="""
---
name: my-workflow-name
description: "简洁描述这个流程做什么"
license: MIT
---

# My Workflow

## Steps

1. ...
2. ...

## Pitfalls

- 容易忘的细节
"""
)
```

### Step 3: 写 test-prompts

```json
# 在 skill 目录下创建 test-prompts.json
[
    {
        "prompt": "test user prompt that would trigger this skill",
        "expected": "description of expected behavior"
    }
]
```

### Step 4: 验证

```bash
# 确认 skill 可加载
skill_view(name="my-workflow-name")
```
