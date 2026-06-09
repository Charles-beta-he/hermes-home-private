# Tree-Shaped Parallel Boundary System — Design Document

## Problem Statement

All 25 UVISA C端 Lark tasks share the boundary key `uvisa-app-2.0:userapp-lark`,
which collapses them into a single conflict group. The dynamic N formula:

    N = min(ceil(dispatchable/7), conflict_groups, MAX_CAP)

yields N=2 (only 2 conflict groups exist). These tasks actually target 9
independent pages/modules and should be able to run in parallel.

## Current Architecture (What We're Changing)

### Data flow
1. Tasks have `parallel_boundary` and `conflict_group` frontmatter fields
2. `task_parallel_boundary_key(task)` computes isolation key (L5803, brain_task_orchestrator.py)
3. `select_parallel_dispatch(max_agents)` uses boundary_key for isolation (L6285)
4. `get_smoothed_n(dispatchable_count, conflict_group_count)` caps N (dynamic_n.py)
5. `classify_batch(tasks)` → `classify_deterministic(task)` → `compute_boundary_key(task)` (task_classifier.py)
6. `prepare_claim_batch()` calls classify_batch, counts groups, feeds to get_smoothed_n

### Key resolution order in `task_parallel_boundary_key` (L5803-5842)
1. explicit `parallel_boundary` field → `boundary:{value}`  ← ALL UVISA tasks hit this
2. `workspace_isolation` = worktree/copy → per-task isolation
3. `conflict_group` + workspace → fine-grained conflict isolation
4. inferred conflict_group + workspace → auto-derived
5. workspace → workspace-level
6. evolution lane + architecture_target
7. project → project-level
8. task id → self-isolating

### Current task structure
```yaml
# All 25+ UVISA C端 tasks have:
parallel_boundary: uvisa-app-2.0:userapp-lark
project: uvisa-app-2.0
# No workspace, no conflict_group set
```

## Design: Tree-Shaped Boundaries

### Core idea
Instead of a flat boundary `uvisa-app-2.0:userapp-lark`, derive a tree-shaped
boundary `project:page` from the task title when the explicit parallel_boundary
uses a known coarse prefix.

    Before: boundary:uvisa-app-2.0:userapp-lark        (all 25+ tasks → 1 group)
    After:  boundary:uvisa-app-2.0:userapp-lark:转入转出  (12 tasks → 1 group)
            boundary:uvisa-app-2.0:userapp-lark:充值理财  ( 9 tasks → 1 group)
            boundary:uvisa-app-2.0:userapp-lark:消息通知  ( 6 tasks → 1 group)
            boundary:uvisa-app-2.0:userapp-lark:资产首页  ( 5 tasks → 1 group)
            boundary:uvisa-app-2.0:userapp-lark:收款人    ( 2 tasks → 1 group)
            boundary:uvisa-app-2.0:userapp-lark:PWA安装   ( 2 tasks → 1 group)
            boundary:uvisa-app-2.0:userapp-lark:Admin后台 ( 1 task  → 1 group)
            boundary:uvisa-app-2.0:userapp-lark:通用UI    ( 1 task  → 1 group)
            boundary:uvisa-app-2.0:userapp-lark:通用      ( 1 task  → 1 group)

Result: 9 groups → N = min(ceil(39/7), 9, 3) = min(6, 9, 3) = **3**

### Verified against actual task titles
Classification tested against all 39 UVISA C端 Lark task titles.
See "Verification" section below for full results.

### Page boundary derivation rules (ordered, first match wins)

| Priority | Pattern (in title)                      | Page Key   | Rationale                          |
|----------|-----------------------------------------|------------|------------------------------------|
| 1        | 转入\|转出\|兑换\|跨境汇款\|跨境        | 转入转出   | Transfer/exchange page             |
| 2        | 充值\|U-VISA\|活期宝\|定期理财\|赎回\|APY\|财富\|持仓\|收益\|理财 | 充值理财 | Topup/wealth page |
| 3        | 资产.*首页\|总资产\|盈亏\|最近交易\|法币钱包\|加密钱包\|交易记录\|交易详情\|订单号\|处理中 | 资产首页 | Asset home page |
| 4        | 收款人\|SWIFT\|电汇\|IBA               | 收款人     | Beneficiary management             |
| 5        | 消息\|通知\|站内信\|横幅\|消息中心\|通知中心 | 消息通知 | Notification center                |
| 6        | 登录页\|注册页\|验证码发送\|邮箱验证\|支付密码\|OTP验证\|安全验证\|登录密码 | 登录验证 | Auth/login flow (specific, not incidental mentions) |
| 7        | PWA\|安装弹窗\|二维码跳转\|桌面app      | PWA安装    | PWA installation                   |
| 8        | admin\|后台\|管理端                     | Admin后台  | Admin panel                        |
| Fallback | 骨架屏\|首屏\|启动图\|底部导航栏\|蓝色方块\|渲染 | 通用UI | Generic UI/shell               |
| Default  | (no match)                              | 通用       | Catch-all (serialized)             |

### Conflict semantics preserved
- Same page key → same boundary → serialized (correct: same page tasks share files)
- Different page key → different boundary → parallel (correct: independent pages)
- Backward compatible: non-UVISA tasks still use their existing boundaries

## Files to Modify

### 1. brain_task_orchestrator.py — `task_parallel_boundary_key` (L5803)

Add tree-refinement step before returning the explicit boundary value.

**Location:** Insert new functions before `task_parallel_boundary_key` (before L5803).
**Change:** Modify the `if explicit:` branch at L5816-5818.

```python
# ── Tree-shaped boundary refinement ────────────────────────────────────────
# Insert BEFORE task_parallel_boundary_key (before L5803)

_UVISA_PAGE_PATTERNS: list[tuple[str, str]] = [
    # (regex, page_key) — first match wins
    (r"(转入|转出|兑换|跨境汇款|跨境)", "转入转出"),
    (r"(充值|U-VISA|活期宝|定期理财|赎回|APY|财富|持仓|收益|理财)", "充值理财"),
    (r"(资产.*首页|总资产|盈亏|最近交易|法币钱包|加密钱包|交易记录|交易详情|订单号|处理中)", "资产首页"),
    (r"(收款人|SWIFT|电汇|IBA)", "收款人"),
    (r"(消息|通知|站内信|横幅|消息中心|通知中心)", "消息通知"),
    (r"(登录页|注册页|验证码发送|邮箱验证|支付密码|OTP验证|安全验证|登录密码)", "登录验证"),
    (r"(PWA|安装弹窗|二维码跳转|桌面app)", "PWA安装"),
    (r"(admin|后台|管理端)", "Admin后台"),
]

_UVISA_PAGE_FALLBACK_PATTERNS: list[tuple[str, str]] = [
    (r"(骨架屏|首屏|启动图|底部导航栏|蓝色方块|渲染)", "通用UI"),
]

_UVISA_COARSE_PREFIXES = [
    "uvisa-app-2.0:userapp-lark",
    "uvisa-app-2.0:userapp",
]


def _refine_boundary_with_page_key(task: Task, explicit_boundary: str) -> str:
    """Refine a coarse explicit boundary with page-level tree key.

    For known coarse boundaries (e.g., uvisa-app-2.0:userapp-lark), extract
    a page-level suffix from the task title to enable parallel dispatch across
    independent pages within the same project.

    Returns the original boundary if no refinement applies.
    """
    is_coarse = any(explicit_boundary.startswith(p) for p in _UVISA_COARSE_PREFIXES)
    if not is_coarse:
        return explicit_boundary

    title = task.title or ""
    mission_title = str(task.fm.get("mission_title") or "")
    haystack = f"{title} {mission_title}"

    for pattern, page_key in _UVISA_PAGE_PATTERNS:
        if re.search(pattern, haystack):
            return f"{explicit_boundary}:{page_key}"

    for pattern, page_key in _UVISA_PAGE_FALLBACK_PATTERNS:
        if re.search(pattern, haystack):
            return f"{explicit_boundary}:{page_key}"

    return f"{explicit_boundary}:通用"
```

**Modify** L5816-5818:
```python
# BEFORE:
    explicit = str(task.fm.get("parallel_boundary") or "").strip()
    if explicit:
        return f"boundary:{explicit}"

# AFTER:
    explicit = str(task.fm.get("parallel_boundary") or "").strip()
    if explicit:
        refined = _refine_boundary_with_page_key(task, explicit)
        return f"boundary:{refined}"
```

### 2. task_classifier.py — `compute_boundary_key` (L133)

Add the same refinement to the classifier so it stays in sync with the orchestrator.

**Location:** Insert new functions before `compute_boundary_key` (before L133).
**Change:** Modify the `if explicit:` branch at L147-149.

```python
# ── Tree-shaped boundary refinement (dict-based) ──────────────────────────
# Insert BEFORE compute_boundary_key (before L133)

_UVISA_PAGE_PATTERNS = [
    (r"(转入|转出|兑换|跨境汇款|跨境)", "转入转出"),
    (r"(充值|U-VISA|活期宝|定期理财|赎回|APY|财富|持仓|收益|理财)", "充值理财"),
    (r"(资产.*首页|总资产|盈亏|最近交易|法币钱包|加密钱包|交易记录|交易详情|订单号|处理中)", "资产首页"),
    (r"(收款人|SWIFT|电汇|IBA)", "收款人"),
    (r"(消息|通知|站内信|横幅|消息中心|通知中心)", "消息通知"),
    (r"(登录页|注册页|验证码发送|邮箱验证|支付密码|OTP验证|安全验证|登录密码)", "登录验证"),
    (r"(PWA|安装弹窗|二维码跳转|桌面app)", "PWA安装"),
    (r"(admin|后台|管理端)", "Admin后台"),
]
_UVISA_PAGE_FALLBACK_PATTERNS = [
    (r"(骨架屏|首屏|启动图|底部导航栏|蓝色方块|渲染)", "通用UI"),
]
_UVISA_COARSE_PREFIXES = [
    "uvisa-app-2.0:userapp-lark",
    "uvisa-app-2.0:userapp",
]


def _refine_boundary_with_page_key_dict(task: dict, explicit_boundary: str) -> str:
    """Dict-based version of tree-shaped refinement for classifier."""
    is_coarse = any(explicit_boundary.startswith(p) for p in _UVISA_COARSE_PREFIXES)
    if not is_coarse:
        return explicit_boundary

    title = str(task.get('title') or task.get('id') or '')
    mission_title = str(task.get('mission_title') or '')
    haystack = f"{title} {mission_title}"

    for pattern, page_key in _UVISA_PAGE_PATTERNS:
        if re.search(pattern, haystack):
            return f"{explicit_boundary}:{page_key}"

    for pattern, page_key in _UVISA_PAGE_FALLBACK_PATTERNS:
        if re.search(pattern, haystack):
            return f"{explicit_boundary}:{page_key}"

    return f"{explicit_boundary}:通用"
```

**Modify** L147-149:
```python
# BEFORE:
    explicit = str(task.get('parallel_boundary') or '').strip()
    if explicit:
        return f'boundary:{explicit}'

# AFTER:
    explicit = str(task.get('parallel_boundary') or '').strip()
    if explicit:
        refined = _refine_boundary_with_page_key_dict(task, explicit)
        return f'boundary:{refined}'
```

### 3. brain_task_orchestrator.py — Dynamic N group counting

Two locations count groups from raw frontmatter instead of actual boundary keys:

**Location A:** `command_parallel_dispatch_dry_run` (L6386-6394)
**Location B:** `command_parallel_claim_and_handoff` (L8028-8035)

Both have this pattern:
```python
# CURRENT:
groups = set()
for t in candidates:
    g = str(t.fm.get("conflict_group") or t.fm.get("parallel_boundary") or "").strip()
    if g:
        groups.add(g)
```

**Change both to:**
```python
# NEW: Count actual boundary keys (after tree refinement)
groups = set()
for t in candidates:
    bk = task_parallel_boundary_key(t)
    if bk:
        groups.add(bk)
```

This ensures the dynamic N calculation sees the refined page-level groups
(9 groups for UVISA) instead of the flat group (1 group).

### 4. dynamic_n.py — No changes needed

The formula already works correctly. The only fix was in the callers
(sections 3 above) passing the correct group count.

Optional future change: increase MAX_CAP from 3 to 4+ if more parallelism needed.

### 5. agent_team_controller.py — `prepare_claim_batch` (L1551) — No changes needed

Uses `classify_batch` → `classify_deterministic` → `compute_boundary_key`.
After change #2, this automatically uses refined boundaries.

## Migration Strategy

### Phase 1: Code changes (immediate)
1. Add `_refine_boundary_with_page_key` to brain_task_orchestrator.py (before L5803)
2. Add `_refine_boundary_with_page_key_dict` to task_classifier.py (before L133)
3. Fix dynamic N group counting at L6386-6394 and L8028-8035
4. Validate: `python3 -m py_compile` on both files

### Phase 2: No frontmatter migration needed
The refinement is applied at READ time (when computing boundary keys), not at
WRITE time. Existing tasks keep their `parallel_boundary: uvisa-app-2.0:userapp-lark`
frontmatter. The tree-shaped suffix is derived dynamically from the title.

Benefits:
- Zero migration risk
- Can be rolled back by removing the refinement functions
- New tasks can optionally set finer-grained parallel_boundary explicitly

### Phase 3: Optional — set explicit page boundaries on new tasks
For future UVISA C端 tasks, the intake process could auto-set:
```yaml
parallel_boundary: uvisa-app-2.0:userapp-lark:转入转出
```
This would make the boundary explicit and skip the inference step.

## Verification Plan

### 1. Classification test (verified in design phase)
39 UVISA C端 Lark tasks classified into 9 groups:
  转入转出: 12 tasks | 充值理财: 9 tasks | 消息通知: 6 tasks
  资产首页: 5 tasks  | 收款人: 2 tasks   | PWA安装: 2 tasks
  Admin后台: 1 task  | 通用UI: 1 task    | 通用: 1 task

### 2. Dry-run dispatch
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --json
```
Expected: selected tasks span 3+ different boundary keys (not 1).

### 3. Classifier consistency check
```bash
python3 ~/.hermes/scripts/task_classifier.py classify --json
```
Expected: UVISA tasks show 9 distinct groups instead of 1.

### 4. Dynamic N test
```bash
python3 ~/.hermes/scripts/dynamic_n.py test
```
Expected: with 39 dispatchable and 9 groups, N = min(6, 9, 3) = 3.

### 5. Regression: non-UVISA tasks unaffected
Verify that tasks with other parallel_boundaries (e.g., uvisa-admin:wealth-product-config:...)
are NOT refined (they don't match the coarse prefix).

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Wrong page key → tasks that share files run in parallel | Low | Page patterns conservative; fallback `:通用` serializes catch-all |
| Classifier/orchestrator divergence | Low | Same patterns in both; boundary consistency check validates |
| Performance of regex on every task | Negligible | ~18 regexes × ~40 tasks = ~720 regex ops per cycle |
| Breaking non-UVISA tasks | None | Refinement only triggers for known coarse prefixes |
| 12 tasks in 转入转出 serialize slowly | Expected | Correct behavior — they share page files; 27 other tasks run in parallel |
