---
name: requirement-clarification
description: "Use when 需求澄清与验收定义 — 接任务时的标准流程。确保理解正确、验收标准明确、边界清晰后再动手。Use when receiving a new task, feature request, or bug report."
license: MIT
tags: [requirements, planning, clarification, acceptance-criteria]
---

# Requirement Clarification — 需求澄清与验收定义

## Overview

需求澄清与验收定义 — 接任务时的标准流程。确保理解正确、验收标准明确、边界清晰后再动手。Use when receiving a new task, feature request, or bug report. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to Use

Use this skill when the request matches the `requirement-clarification` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

> 接任务时先对齐再动手。理解错了就做错了——先对齐再动手。


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## 何时使用

- 收到新需求/功能请求
- 接到 bug 报告
- 任务描述模糊或缺少验收标准
- 用户说"帮我做个 XXX"但没有细节
- UI/样式任务使用"对齐"、"调整"、"优化"、"处理一下"、"样式一致"、"参考其他页面"等模糊描述，且目标对象、参考对象、对齐维度、验收方式未完全明确

## 核心原则

**不澄清不动手。** 任务描述越短，澄清工作越重要。

## 五步澄清法

### Step 1: 复述需求

用自己的话复述用户要做什么，确保理解一致。

输出格式：
```
我理解的你的需求是：
[一句话目标]

涉及的范围：
- [范围1]
- [范围2]

是这样吗？
```

### Step 2: 定义验收标准 (AC)

每个需求必须有可验证的验收标准。

**好的 AC：**
- [ ] 用户在 375px 和 1280px 视口下都能正常提交表单
- [ ] 提交后显示成功 toast，3 秒后自动消失
- [ ] 表单验证错误时，对应字段边框变红并显示错误文案

**差的 AC：**
- [ ] 表单能正常工作（无法验证）
- [ ] UI 好看（主观，无法验证）

如果用户没给 AC，主动补充并确认。

### Step 2.5: UI 模糊对齐澄清门

当任务涉及 UI/样式"对齐"但缺少关键信息时，必须在进入 Step 3 前补齐以下问题；不要把截图里的意图、参考页面或验收标准藏成自己的假设。

1. **对齐对象** — 具体页面、组件、文件或截图区域是什么？
2. **参考对象** — 要对齐哪个页面、组件、设计稿、截图或既有 primitive？
3. **对齐维度** — 对齐布局、尺寸、颜色、字体、边框、圆角、阴影、间距、动效、数据文案、交互行为中的哪些？
4. **交互态覆盖** — 需要覆盖 default / hover / focus / selected / open / expanded / disabled / error / popup / listbox / portal 中哪些状态？
5. **验收方式** — 用参考截图、浏览器截图、DOM/CSS read-back、视觉 diff、静态脚本或测试命令中的哪一种验收？
6. **组件溯源** — 参考 UI 使用的是什么组件库/primitive system？当前实现是否改到了真实渲染的组件、弹层或样式层？

如果可从用户截图、代码路径、项目约定中可靠恢复这些信息，可以显式写出"按截图/代码推断为 X"并继续执行；否则先问用户。此门专门防止只改 `data-prd` / mock / copy / 文档，却没改真实组件、弹层或样式层的失败模式。

### Step 3: 明确边界

定义**在范围内**和**不在范围内**：

```
### IN SCOPE（做）
- 功能 A
- 功能 B

### OUT OF SCOPE（不做）
- 功能 C（建议后续迭代）
- 功能 D（超出当前资源）
```

### Step 4: 识别依赖与风险

- 依赖：需要哪些外部资源/接口/权限？
- 风险：哪些因素可能导致延期或失败？
- 假设：基于哪些假设在做这个方案？

### Step 5: 确认优先级

- P0: 阻塞发布，必须做
- P1: 重要，尽量做
- P2: 锦上添花，有时间做

## 输出物

澄清完成后，产出 `.claude/requirements/{task-id}.md`：

```markdown
# 需求澄清 — [Task 标题]

## 需求复述
[一句话 + 详细描述]

## 验收标准 (AC)
- [ ] AC1: [可验证标准]
- [ ] AC2: [可验证标准]

## 边界定义
### IN SCOPE
- [ ]
### OUT OF SCOPE
- [ ]

## 依赖与风险
- 依赖: [ ]
- 风险: [ ]
- 假设: [ ]

## 优先级
- [ ] P0 / P1 / P2

## 下一步
- [ ] 进入 writing-plans / 直接执行
```

## 快速澄清清单

简单任务（< 30 分钟）可以跳过文档，但必须口头确认：
- [ ] 我理解的目标对吗？
- [ ] 验收标准是什么？
- [ ] 有什么不能碰的？

## 与 PUA 体系的集成

- P10: 在战略层面定义需求价值
- P9: 在任务拆解前确保需求澄清完成
- P8/P7: 执行前阅读需求澄清文档

## 反模式

- ❌ 不问清楚就开始写代码
- ❌ 假设用户想要的是 X，实际用户想要的是 Y
- ❌ 验收标准模糊，做完后用户说"不是我要的"
- ❌ 范围蔓延——做着做着加了新功能

## Common Pitfalls

1. Advancing stages without a gate, evidence artifact, or closure-state check.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
