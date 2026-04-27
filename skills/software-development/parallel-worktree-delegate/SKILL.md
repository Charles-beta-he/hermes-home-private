---
name: parallel-worktree-delegate
description: "创建独立 git worktree 并行执行多个任务，每个子 agent 在独立工作区修改，完成后合并回主干。"
license: MIT
tags: [parallel, git, worktree, delegate, merge]
---

# Parallel Worktree Delegate

> 利用 git worktree + delegate_task 实现真正并行的多任务开发

## When to Use

- 用户要求同时修改多个不冲突的模块/文件
- 需要并行验证多个方案
- 希望在子任务失败时不影响主工作区

## Process

### Prerequisites

确认 git 仓库无未提交修改（如有，先 commit 或 stash）:

```bash
git status --porcelain
```

### Step 1: 为每个子任务创建 worktree

```bash
# 为每个 task 创建一个独立工作区
git worktree add /tmp/wt-{task-name} {base-branch}

# 进入 worktree
cd /tmp/wt-{task-name}
```

### Step 2: 用 delegate_task 派发并行任务

每个子 agent 在独立 worktree 中工作:

```python
# 主 agent 流程
tasks = [
    {
        "goal": "修改模块 A 的 xxx 功能",
        "context": f"在 /tmp/wt-task-a 目录中修改，完成 git add + commit"
    },
    {
        "goal": "修改模块 B 的 yyy 功能",
        "context": f"在 /tmp/wt-task-b 目录中修改，完成 git add + commit"
    },
]
results = delegate_task(tasks=tasks, toolsets=["terminal", "file"])
```

### Step 3: 收集并合并

```bash
# 记录每个 worktree 的 commit hash
cd /tmp/wt-task-a && git rev-parse HEAD
cd /tmp/wt-task-b && git rev-parse HEAD

# 在主工作区合并
cd {main-repo}
git merge /tmp/wt-task-a --no-edit
git merge /tmp/wt-task-b --no-edit
```

### Step 4: 清理

```bash
git worktree remove /tmp/wt-task-a
git worktree remove /tmp/wt-task-b
```

## Pitfalls

- **文件冲突**: 两个 task 改了同一个文件 → git merge 会冲突，需手动解决
- **worktree 需要独立 branch**: 每个 worktree 在一个独立分支上工作
- **delegate_task 有并发上限**: 默认 3 个并发子 agent，超过的排队
- **子 agent 无用户交互能力**: 不能在里面用 clarify
