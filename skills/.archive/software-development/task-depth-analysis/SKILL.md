---
name: task-depth-analysis
description: "Use when classify task depth/complexity using multi-layer signal extraction, project profile domain mapping, and multimodel consensus. Use when analyzing task pools, backlog triage, or estimating implementation effort for a batch of tasks."
triggers:
  - task classification / 分类 / tier assignment
  - iceberg analysis / 冰山分析
  - backlog triage / task pool analysis
  - "which tasks need backend work"
  - "is this frontend-only or fullstack"
  - task depth estimation / complexity tiering
---

# Task Depth Analysis (Iceberg Classification)

## Overview

Classify task depth/complexity using multi-layer signal extraction, project profile domain mapping, and multimodel consensus. Use when analyzing task pools, backlog triage, or estimating implementation effort for a batch of tasks. This skill is maintained as a `pipeline`-shaped contract: it should guide ordered multi-stage work with gates, evidence, retries, and closure states without stealing adjacent workflows or relying on unstated assumptions.

Systematic methodology for classifying tasks into depth tiers based on evidence from codebase structure, project profiles, and domain knowledge.

## When to Use

- Analyzing a batch of tasks (Lark/Linear/GitHub issues) for implementation planning
- Determining which tasks need backend work vs frontend-only
- Backlog triage when tasks have vague or surface-level descriptions
- Building a work plan that respects architectural boundaries

## Architecture: Three-Layer Classification

```
Layer 1: Deterministic Signal Extraction
  ├── Codebase signals (file paths, class names, API endpoints)
  ├── Semantic signals (Chinese/English domain keywords)
  └── Behavioral signals (交互/点击/跳转 → UI; 保存/记录/同步 → logic)

Layer 2: Project Profile Integration
  ├── fullstack_domain_map → domain has backend services?
  ├── conventions → architecture constraints (e.g. "前后端是一个项目")
  └── Controller/Service presence → mark as L if touched

Layer 3: Multimodel Consensus (for low-confidence tasks)
  ├── Send task description + codebase context to 3+ models
  ├── Each model independently classifies
  └── Majority vote → final tier (overrides L1/L2 for targeted tasks)
```

## Tier Definitions

| Tier | Meaning | Signals |
|------|---------|---------|
| S0   | Simple UI — single component, no state | Display-only, formatting, static content |
| S1   | Compound UI — multiple components, local state | Multi-step UI, local state management, cross-component |
| F    | Frontend logic — API calls, state management | API integration, complex state, frontend business logic |
| L    | Requires backend — data persistence, service changes | Backend service, DB writes, API contract changes |

## Critical Workflow Order

```
1. Run deterministic classifier on ALL tasks
2. Run project profile integration on ALL tasks
3. Write batch results to task frontmatter
4. Identify low-confidence tasks (confidence != "high" or != "multimodel_consensus")
5. Run multimodel consensus ONLY on low-confidence tasks
6. Write multimodel results (override batch results for those specific tasks)
```

**PITFALL: Steps 3 and 6 ordering matters.** If you run multimodel consensus first (step 5-6) then batch update (step 3), the batch update overwrites multimodel results. ALWAYS run batch first, multimodel second.

## Signal Extraction Patterns

### Semantic Indicators (Chinese)

```python
# Display-only → likely S0/S1
S0_KEYWORDS = ["样式", "展示", "格式", "颜色", "位置", "对齐", "图标", "间距", "弹窗"]
S1_KEYWORDS = ["切换", "多状态", "标签页", "筛选", "列表+详情", "步骤"]

# Logic indicators → likely F
F_KEYWORDS = ["调用", "保存", "获取", "接口", "状态", "缓存", "计算"]

# Backend indicators → likely L
L_KEYWORDS = ["写入", "修改数据", "删除", "创建", "同步", "审核", "审批", "权限", "登录"]
```

### Codebase Signals

- File path contains domain name (e.g., `wallet/`, `exchange/`) → check if domain has backend
- Class name mentions Controller/Service → L tier
- Pure component files (Button, Card, Modal) → S0/S1
- API call files (useXxx hooks, api/xxx.ts) → F tier

## Project Profile Integration

When a project profile has `fullstack_domain_map`:

```python
# 1. Extract domains that have backend services
domains_with_backend = set()
for domain, paths in domain_map.items():
    if domain.startswith("_"):
        continue
    if isinstance(paths, dict) and paths.get("backend"):
        domains_with_backend.add(domain)

# 2. Map Chinese business keywords to domains
domain_keywords = {
    "wallet": ["钱包", "余额", "钱包流水"],
    "exchange": ["兑换", "汇率", "换汇"],
    "remit": ["汇款", "收款人", "跨境"],
    # ... per-project
}

# 3. When task mentions a domain with backend → signal L
```

**PITFALL: `domain_map` may have `_description` key (string, not dict).**
Always check `isinstance(paths, dict)` before calling `.get()`.

**PITFALL: Controller names are in English, task descriptions often in Chinese.**
Don't try to match `AuthController` against Chinese task titles. Instead, build a Chinese keyword → domain mapping from the domain_map's semantic meaning.

## Writing Results to Task Frontmatter

Task files should carry classification in YAML frontmatter:

```yaml
iceberg_tier: L
iceberg_scope: requires_backend
iceberg_domain: wallet
iceberg_confidence: high
```

Confidence values:
- `high` — clear signal, no ambiguity
- `medium` — some signals, needs review
- `low` — weak signals, candidate for multimodel
- `multimodel_consensus` — classified by model voting

## Pitfalls

1. **Batch overwrite kills multimodel results.** Run deterministic batch FIRST, multimodel consensus SECOND. See Critical Workflow Order above.

2. **domain_map `_description` is a string.** `domain_map["_description"]` is not a dict — check `isinstance(paths, dict)` before `.get("backend")`.

3. **Chinese ↔ English mismatch.** Project profiles use English file paths (AuthController, WalletController). Task descriptions are in Chinese (登录, 钱包). Build a bilingual keyword bridge, don't expect direct string matching.

4. **"涉及某域" ≠ "需要改后端".** A task mentioning "钱包" might be pure UI (balance display). The domain_map signal says "wallet HAS a backend" not "this task MUST touch backend". Use domain signal as a boost (+2 weight) not an override — let other signals (display-only, formatting) compete.

5. **Over-classification risk.** When project profile integration adds many L signals, verify the remaining F tasks are genuinely frontend-only. Spot-check 2-3 F tasks against actual codebase to calibrate.

6. **Multimodel cost control.** Only send low-confidence tasks to multimodel, not the entire batch. For 40 tasks, expect ~5-10 low-confidence candidates.

## Verification

After classification:
1. Dashboard should show all tiers represented (if only one tier, something is wrong)
2. Spot-check 3 random L tasks: do they actually touch backend code?
3. Spot-check 2 random F tasks: are they truly frontend-only?
4. Total count should match active tasks in pool
5. No task should have `confidence: low` without multimodel review

## References

See `references/uvisa-implementation.md` for the complete implementation used on the uvisa project (41 Lark tasks, 10 domains, 3-layer classification).
