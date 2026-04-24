---
name: framework-audit
description: "第三方 AI 系统/框架评估与引入决策框架 — 系统化分析外部 AI 工具（开发框架、工作流系统、CLI 工具），给出引入建议、选择性借鉴方案和集成步骤。Use when evaluating a GitHub repo, npm package, or AI tool for adoption. Triggers: '评估框架', '引入第三方', '工具选型', '框架分析', '是否引入', '对比分析', '技术选型', 'adoption analysis', 'framework evaluation'."
license: MIT
tags: [framework-audit, third-party, evaluation, adoption, integration, decision-framework]
---

# Framework Audit — 第三方 AI 系统评估与引入决策

> 不要因为一个工具流行就引入。评估 → 决策 → 选择性借鉴 → 集成。

## 核心流程

```
[1] 信息收集    → [2] 多维度分析    → [3] 引入决策    → [4] 选择性借鉴    → [5] 集成与验证
```

---

## Phase 1: 信息收集

### 1.1 仓库结构分析

```bash
# 快速了解项目规模
git clone --depth 1 <repo-url> /tmp/<repo-name>
find /tmp/<repo-name> -type f | wc -l          # 文件总数
du -sh /tmp/<repo-name>                         # 总大小
ls /tmp/<repo-name>                             # 根目录结构
```

关键观察点：
- 总文件数 > 500 → 大型项目，引入成本高
- 包含 hooks/SDK/CLI → 深度绑定特定运行时
- 多语言 README → 社区活跃度高
- 有 IDE 配置文件 → IDE 深度集成

### 1.2 核心理念理解

阅读以下文件（按优先级）：
1. `README.md` 前 200 行（解决的问题 + 核心卖点）
2. `package.json`（依赖、脚本、bin 命令）
3. 核心工作流文件（通常是 `workflows/` 或 `commands/`）
4. 一个代表性 agent/skill 的完整定义

**关键问题清单**：
- 这个工具解决什么问题？
- 它的核心理念是什么？（spec-driven? context-engineering? wave-execution?）
- 它与现有体系的关系是什么？替代/补充/冲突？
- 它的运行环境要求是什么？

### 1.3 兼容性检查

| 检查项 | 方法 | 不兼容处理 |
|--------|------|-----------|
| 运行时兼容性 | 检查是否绑定特定 IDE/CLI | 评估适配成本 |
| 路径硬编码 | 搜索 `.claude/` 等特定路径 | 批量替换为 Hermes 路径 |
| 依赖项 | `package.json` dependencies | 检查本地是否已安装 |
| Node 版本 | `engines.node` | 确认 >= 系统版本 |
| 术语冲突 | 检查与现有 skill 的重叠命名 | 统一术语或保留原名 |

---

## Phase 2: 多维度分析

### 2.1 对比分析矩阵

| 维度 | 当前工作流 | 新框架 | 差异评估 |
|------|-----------|--------|---------|
| 目标场景 | | | |
| 架构模式 | | | |
| 规模 | | | |
| 运行时 | | | |
| 验证体系 | | | |
| 迭代模式 | | | |
| 社区/维护 | | | |
| 引入成本 | — | — | 高/中/低 |

### 2.2 引入价值评估

**评分制（1-10）**：

| 维度 | 权重 | 评分标准 |
|------|------|---------|
| 理念互补性 | 25% | 是否填补了现有体系的空白 |
| 技术可集成性 | 20% | 能否与现有 skill 协同工作 |
| 维护成本 | 20% | 引入后的持续维护工作量 |
| 运行时兼容性 | 15% | 是否需要改变现有工作方式 |
| 社区活跃度 | 10% | Star 数、更新频率、贡献者 |
| 文档质量 | 10% | 是否易于理解和使用 |

**总分 = Σ(维度分 × 权重) / 10**，满分 100

**决策阈值**：
- >= 80: 值得整体引入（但需分阶段）
- 60-79: 选择性借鉴组件
- < 60: 仅做参考，不引入

### 2.3 冲突分析

**常见冲突类型**：

1. **运行时冲突** — 框架依赖特定 CLI/IDE
   - 处理: 评估适配成本，或使用兼容层

2. **理念冲突** — 框架是"一套系统统治所有" vs 现有是"自由组合"
   - 处理: 提取可复用组件，放弃整体架构

3. **规模冲突** — 框架 9MB+ vs 现有轻量级生态
   - 处理: 只引入核心文件，忽略示例/文档/测试

4. **目标冲突** — 框架为"构建项目"设计 vs 现有为"进化 Agent"
   - 处理: 明确分工，不重叠使用

---

## Phase 3: 引入决策

### 3.1 决策树

```
总分 >= 80?
  ├─ 是 → 是否改变现有工作方式?
  │       ├─ 是 → 分阶段引入，先试点
  │       └─ 否 → 全局安装，逐步迁移
  └─ 否 → 总分 >= 60?
          ├─ 是 → 选择性借鉴（见 Phase 4）
          └─ 否 → 仅做参考，不引入
```

### 3.2 决策输出格式

```
═══════════════════════════════════════════════════════════════════
                    评估结论: {整体引入 / 选择性借鉴 / 不引入}
═══════════════════════════════════════════════════════════════════

评分: {X}/100 ({A/B/C/D} 级)

建议行动:
  1. {具体行动}
  2. {具体行动}

风险:
  - {风险1} → 缓解: {措施}
  - {风险2} → 缓解: {措施}

如果选择选择性借鉴，推荐组件:
  1. {组件1} → 引入方式: {方式} → 成本: {高/中/低}
  2. {组件2} → 引入方式: {方式} → 成本: {高/中/低}
```

---

## Phase 4: 选择性借鉴

当决定不整体引入时，从框架中提取高价值组件：

### 4.1 组件提取流程

```
Step 1: 识别核心组件
  → 列出框架的所有子系统（workflow/agent/command/hook）
  → 评估每个子系统的独立价值

Step 2: 评估可移植性
  → 该组件是否依赖框架的其他部分？
  → 提取后能否独立工作？
  → 与现有 skill 的集成成本？

Step 3: 设计集成方案
  → 直接引入为独立 skill
  → 融入现有 skill 的 references/ 目录
  → 作为方法论写入现有 skill

Step 4: 最小可行集成
  → 提取核心逻辑（通常 < 300 行）
  → 适配到 Hermes 环境
  → 保留原框架的引用和署名
```

### 4.2 常见借鉴模式

| 原框架组件 | 借鉴方式 | 集成目标 |
|-----------|---------|---------|
| Wave Execution | 修改 loop skill | 迭代并行化 |
| Context Engineering | 融入 cognitive-load-agent | Context 预算优化 |
| Verification Workflow | 增强 post-deploy-verification | 验证闭环 |
| Agent Routing | 新建 dispatcher skill | 智能命令路由 |
| Agent Design Pattern | 阅读借鉴 | Skill 升级参考 |

---

## Phase 5: 集成与验证

### 5.1 安装步骤

**全局安装**（适用于可独立运行的 CLI 工具）：
```bash
npx <package>@latest --<runtime> --global
# 或从源码构建
npm run build:sdk
node bin/install.js --<runtime> --global
```

**本地集成**（适用于 skill/agent 文件）：
```bash
# 1. 复制到 Hermes skill 目录
cp -r <repo>/agents/* ~/.hermes/skills/
# 2. 适配路径和术语
# 3. 初始化追踪文件
touch ~/.hermes/skills/<skill-name>/results.tsv
```

### 5.2 安装后验证

```bash
# 1. 检查文件是否到位
ls ~/.claude/skills/ | grep "<prefix>" | wc -l

# 2. 检查 SDK 是否可用
<sdk-command> --version

# 3. 检查配置文件是否正确加载
# 4. 执行一次完整工作流测试
```

### 5.3 常见安装问题

| 问题 | 原因 | 解决 |
|------|------|------|
| SDK dist 不存在 | 未运行 build:sdk | `cd sdk && npm ci && npm run build` |
| Hooks 缺失 | build:hooks 未执行 | `npm run build:hooks` |
| 路径权限拒绝 | MCP filesystem 沙盒 | 使用 terminal 工具替代 |
| 运行时找不到 | 未在 PATH 中 | `npm link` 或绝对路径调用 |
| 术语冲突 | 与现有 skill 命名重叠 | 重命名或添加命名空间 |

---

## 输入输出规范

### 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `repo_url` | string | 是 | GitHub 仓库 URL 或 npm 包名 |
| `action` | enum | 是 | `analyze` / `decide` / `integrate` |
| `scope` | enum | 否 | `full` / `selective` / `reference-only` |
| `components` | string[] | 否 | 指定要分析的子系统（selective 时必填）|

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `score` | float | 0-100 引入价值评分 |
| `grade` | enum | A/B/C/D |
| `decision` | enum | adopt / selective / reject |
| `components` | object[] | 各子系统的评分和建议 |
| `risks` | object[] | 风险列表 + 缓解措施 |
| `integration_plan` | string[] | 集成步骤（如 decision=adopt/selective）|

---

## 使用方式

### 评估一个 GitHub 仓库
```
用户: "分析 https://github.com/xxx/yyy 是否值得引入"
→ Phase 1-3 完整流程
→ 输出: 评分 + 决策 + 风险 + 建议行动
```

### 选择性借鉴组件
```
用户: "从 GSD 中提取 wave execution 概念"
→ Phase 1 (快速扫描) + Phase 4 (组件提取)
→ 输出: 提取方案 + 集成步骤 + 成本评估
```

### 技术选型对比
```
用户: "对比 GSD vs Taskmaster vs OpenSpec"
→ 对多个框架执行 Phase 1-2
→ 输出: 对比矩阵 + 推荐方案
```

---

## 与现有体系集成

### 与 darwin-skill 集成
- 引入价值评分中的 "理念互补性" 使用 Darwin 的 8 维度 rubric 评估
- 组件提取后的 skill 直接进入 Darwin 优化循环

### 与 bayesian-agent 集成
- 引入决策的置信度随实际使用效果更新
- 高评分但实际效果差 → beta 增加，降级决策

### 与 p10 集成
- 框架引入属于战略决策，需 P10 审查
- 大规模引入（>50 个文件）需单独规划

---

## 输出物

- 评估报告（本次分析的结构化输出）
- 集成计划（如决定引入）
- 风险登记册
- 组件提取方案（如选择性借鉴）

## 约束

- 遵循项目规范
- 在 context budget 内完成
