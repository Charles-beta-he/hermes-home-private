# PilotDeck 差距分析：Hermes 自强化机会

## 源信息
- **仓库**: https://github.com/OpenBMB/PilotDeck
- **官网**: https://pilotdeck.openbmb.cn/
- **描述**: Task-oriented AI Agent productivity platform
- **星标**: 1.9k
- **分支**: 12
- **语言**: TypeScript/JavaScript, Python
- **许可证**: 未明确显示

## 架构信号

### 核心架构单元：WorkSpace
每个项目拥有独立的文件系统、记忆存储、技能集，实现项目间的完全隔离：
- 平行任务运行不会互相干扰
- 技能会随任务积累自然生长
- 避免全局上下文污染

### 四大核心能力组件

1. **白盒可追溯记忆（Traceable White-box Memory）**
   - 记忆的生成、提取、存储、检索全流程可视化可追溯
   - 当AI出现记忆错误时，可直接定位并编辑对应记忆条目
   - 支持一键回滚
   - 内置Dream Mode可以在空闲窗口合并记忆，避免记忆冲突

2. **智能路由与成本优化（Smart Routing & Cost Optimization）**
   - 自动检测任务难度
   - 复杂任务自动分配给顶级模型（如Claude 3.5 Opus）
   - 简单任务使用轻量模型（如Claude 3.5 Sonnet）
   - 支持设备端/云端协同
   - 在保证任务质量的前提下，将Token消耗降低70%左右

3. **后台常驻执行（Always-on Background Execution）**
   - Agent可以脱离用户主动交互独立运行
   - 自动完成任务后，会以「本地文件+汇总报告」的形式输出结果
   - 支持长周期任务的后台执行

4. **原生MCP协议支持**
   - 整个系统原生兼容Model Context Protocol（MCP）
   - 在Web、CLI、IM三端保持行为一致性
   - 支持与所有支持MCP的服务器集成

## Hermes 当前差距

### 1. WorkSpace 隔离
- Hermes 有项目配置（project-profiles）但没有真正的文件系统隔离
- 任务池是全局的，没有按项目隔离
- 技能是全局共享的

### 2. 白盒记忆系统
- Hermes 有持久化记忆，但不是全流程可视化
- 没有记忆编辑/回滚界面
- 没有类似 Dream Mode 的记忆合并机制

### 3. 智能路由与成本优化
- Hermes 有多模型架构（Codex/Claude/DeepSeek/MiMo）
- 但没有基于任务复杂度的自动路由
- 成本优化是手动配置的

### 4. 后台常驻执行
- Hermes 有 cron 任务和后台进程
- 但没有"本地文件+汇总报告"的标准输出格式
- 没有统一的后台任务监控界面

### 5. MCP 原生支持
- Hermes 有 MCP 客户端支持
- 但不是原生集成，是通过 mcporter 桥接
- 没有 Web/CLI/IM 三端一致性

## 可吸收机制

### 高价值（立即可借鉴）
1. **任务复杂度自动检测** → 改进 Hermes 的多模型路由
2. **成本优化策略** → 为不同优先级任务选择合适模型
3. **后台任务标准化输出** → 统一 Hermes 后台任务的结果格式

### 中等价值（需要适配）
1. **WorkSpace 隔离概念** → 项目级任务池/技能隔离
2. **白盒记忆编辑** → 记忆管理界面
3. **MCP 原生集成** → 深化 Hermes 的 MCP 支持

### 低价值（观察但不急于吸收）
1. **Dream Mode** → 记忆合并可能引入复杂性
2. **Web UI** → Hermes 以 CLI 为主，UI 是可选增强

## 最小可验证集成切片

**任务**: 为 Hermes 添加基于任务复杂度的自动模型路由

**范围**:
1. 分析 PilotDeck 的智能路由算法
2. 设计 Hermes 的任务复杂度评估标准
3. 实现简单的路由规则：P0/P1 → Claude, P2/P3 → MiMo
4. 添加成本监控和回退机制

**验证**:
- 路由决策可追溯
- 成本降低可测量
- 任务质量不下降

## 红线/反漂移约束

1. **不引入重型依赖** → 保持 Hermes 轻量级
2. **不改变 CLI 优先原则** → UI 是可选增强
3. **不破坏现有工作流** → 渐进式改进
4. **不存储敏感信息** → 记忆/路由数据本地化

## 后续任务形状

**主任务**: PilotDeck 架构分析与 Hermes 差距映射
**子任务**:
1. 深入分析智能路由算法
2. 设计任务复杂度评估标准
3. 实现原型路由规则
4. 成本效益分析

## 来源证据

- GitHub 仓库结构：src/, ui/, tests/, scripts/, skills/, assets/
- README 核心特性：WorkSpace 隔离、白盒记忆、智能路由、后台执行、MCP 支持
- 官网展示：使用案例、快速开始、文档、研究论文
- 技术栈：TypeScript/JavaScript + Vite (前端), Python (后端), Docker (部署)