---
name: token-saver-rtk
description: "Use when 全架构 token 优化 21 层: CASI + Token-Eff + RTK + Caveman + Tool Schema + Task Router + Anatomy + Cerebrum + Result Spiller + Dynamic Thinking + Locale Bookend + Tool Output Pipeline + Budget Meter + Query Intent + Deterministic Bypass + Pattern Retrieve。来自 OpenWolf/DeepSeek-TUI/GBrain/Ruflo。."
triggers:
  - "省 token"
  - "token saving"
  - "compress output"
  - "rtk"
  - "caveman"
  - "token optimization"
  - "CASI"
  - "deterministic bypass"
  - "pattern retrieve"
  - "ruflo"
---

# Token Saver: 全架构优化 (21层)

## Overview

全架构 token 优化 21 层: CASI + Token-Eff + RTK + Caveman + Tool Schema + Task Router + Anatomy + Cerebrum + Result Spiller + Dynamic Thinking + Locale Bookend + Tool Output Pipeline + Budget Meter + Query Intent + Deterministic Bypass + Pattern Retrieve。来自 OpenWolf/DeepSeek-TUI/GBrain/Ruflo。. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to Use

Use this skill when the request matches the `token-saver-rtk` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## 新增 (来自 Ruflo)

### Deterministic Bypass (agent/deterministic_bypass.py)
· Tier 0: 确定性任务完全跳过 LLM, $0 成本, <1ms
· 支持变换: var→const, add-semicolons, remove-console, sort-imports, type-hints
· 置信度 ≥0.5 → 执行, <0.5 → 升级到 LLM
· 1500-3000x 加速 (vs Sonnet/Opus)

### Pattern Retrieve (agent/pattern_retriever.py)
· 执行前从记忆检索相似任务
· Jaccard 相似度匹配 (阈值 0.3)
· 成功后存储模式供未来复用
· 缓存: ~/.hermes/cache/patterns/

## 全架构 21 层

```
User Message
  → Deterministic Bypass (Tier 0, $0)
  → Pattern Retrieve (检索历史模式)
  → Query Intent (regex, 零成本)
  → Task Router (complexity → model)
  → Budget Meter (成本门控)
  ↓
System Prompt (Prefix-Cache 友好):
  ├─ Stable tier (byte-stable, 1h cache)
  ├─ Context tier (CASI filtered)
  └─ Volatile tier
  ↓
Tool Outputs:
  ├─ terminal → RTK
  ├─ read_file → Anatomy Scanner
  ├─ 大结果 → Result Spiller (var_handle)
  ├─ 中结果 → compress_tool_output
  └─ Cerebrum → prevent mistakes
  ↓
Assistant Response: Caveman
  ↓
Delegate Task: Task Router per-task
  ↓
Post-task: Pattern Store (DISTILL)
  ↓
History: Compression
```

## 来源汇总
  自研: CASI, Token-Eff, RTK, Caveman, Compression, Prefix Cache, Tool Pipeline
  OpenWolf: Anatomy Scanner, Cerebrum
  LiteLLM: Task Router
  DeepSeek-TUI: Result Spiller, Dynamic Thinking, Locale Bookend
  GBrain: Budget Meter, Query Intent
  Ruflo: Deterministic Bypass, Pattern Retrieve

## 效果
| 指标 | Before | After | 节省 |
|---|---|---|---|
| System prompt | 44K | 12K | -73% |
| Tool outputs | 30K | 5K | -83% |
| Replies | 69 tok | 19 tok | -72% |
| Cache hit rate | ~50% | ~90% | +80% |
| 确定性任务 | LLM调用 | $0, <1ms | -100% |
| 模式复用 | 无 | 检索+复用 | -50% |
| **Total tokens** | **192K** | **60K** | **-69%** |
| **Total cost** | **$0.58** | **$0.15** | **-74%** |

## Frontend Variant

For React/Vue frontend projects (uvisa-app-2.0, uvisa-admin), load `token-saver-frontend-rtk` instead — it has index-first file reading, frontend-specific CASI rules, and backend verification patterns. Layer 1-2 rules are shared via `references/rtk_layer12_fewshot.md`.

## Common Pitfalls

1. Advancing stages without a gate, evidence artifact, or closure-state check.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
