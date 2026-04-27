# Conway 逆定律：组织决定系统

> Melvin Conway, *How Do Committees Invent?* (1968)
> "逆"操作版本: *Inverse Conway Maneuver* (ThoughtWorks, 2010+)
> 联系：[[02-治理理论/Ostrom-公地治理8原则|Ostrom]] ｜ [[04-技能生态/skill-steward角色定义|Skill Steward]]

## 核心命题

**Conway 原定律：** 系统的结构反映组织的沟通结构。

**Conway 逆定律：** 如果你想要一个系统结构，先建立一个能产出该结构的组织。

## 当前组织 → 系统映射

```
当前组织: 无治理（没有"技能委员会"）
     ↓
当前系统: 无治理的代码镜像
     ├── 谁都能创建    → 技能泛滥
     ├── 谁都不删除    → 无淘汰
     └── 无人检查冲突  → 12 个 pua 副本
```

## 目标组织 → 系统映射

```
目标组织: 有 Skill Steward 治理角色
     ↓
目标系统: 有自净化能力的技能生态
     ├── Steward 每天扫描  → 淘汰 & 合并
     ├── Steward 的 KPI    → 生态健康度（非技能数）
     └── Steward 有工具    → 标记废弃、强制合并、冲突报告
```

## Skill Steward 角色定义

### 职责
- **每日扫描**：检测新僵尸、新冲突、新断裂引用
- **每周清理**：执行梯度制裁（DEPRECATED → ARCHIVED）
- **每月报告**：生态健康度仪表盘更新
- **按需仲裁**：同名冲突时决定合并策略

### 执行方式（完全自动化）
```cron
schedule: "0 2 * * *"           # 每日凌晨 2 点
prompt: "Run skill-steward audit: 
  1. Check for stale skills (30d no load)
  2. Check for duplicate names
  3. Check for broken references
  4. Update health dashboard
  5. Report violations"
```

### 组织保障
- Steward 不对任何人汇报（自治权被认可 — Ostrom 原则 7）
- Steward 不可以被创建技能的操作覆盖（检查点一致 — Ostrom 原则 3）

## 制度执行方法

Conway 逆的执行不是一次性的，是通过 **cronjob 持续施加组织力**：

```
每天 2:00: skill-steward audit
每天 2:30: 如果熵债 > 阈值 → 自动 ARCHIVE 最老的 3 个 DEPRECATED skill
每周一 9:00: 生成生态健康周报
每周一 9:30: 推送周报到 Obsidian vault
每月 1 日: 生成理论覆盖矩阵更新
```

每一轮 cronjob 都在**重塑组织结构**，而组织结构持续映射回系统结构。

## 引用

> Conway, M. E. (1968). "How do committees invent?" *Datamation*, 14(4), 28-31.
