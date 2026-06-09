# Tree-Shaped Boundary Refinement

## Problem

When many tasks share the same coarse `parallel_boundary` (e.g. `uvisa-app-2.0:userapp` or `project:uvisa-app-2.0-work`), the dynamic-N formula sees only 1-2 groups and caps concurrency at 2, even when 28+ tasks are clearly separable by page/feature.

## Solution: Content-Based Read-Time Refinement

Refine boundaries at **read time** by extracting page/feature keys from task titles. The frontmatter stays immutable (zero-migration).

### Architecture

```
Frontmatter (immutable)     Read-time refinement (computed)
─────────────────────────   ─────────────────────────────────
parallel_boundary:           task_parallel_boundary_key(t):
  project:uvisa-app-2.0-work → project:uvisa-app-2.0-work:转入转出

Title: "用户端-兑换-USDT 兑换 CNY..."
```

### Anti-patterns (DO NOT USE)

**Anti-pattern 1: Hardcoded prefix list**
```python
# WRONG: every new boundary needs a code change
_UVISA_COARSE_PREFIXES = [
    "uvisa-app-2.0:userapp-lark",
    "uvisa-app-2.0:userapp",
    "project:uvisa-app-2.0-work",
]
```

**Anti-pattern 2: Hardcoded page patterns in orchestrator code**
```python
# WRONG: project-specific regex patterns embedded in orchestrator
_UVISA_PAGE_PATTERNS = [
    (r"(转入|转出|兑换|跨境汇款|跨境)", "转入转出"),
    (r"(充值|U-VISA|活期宝|定期理财|赎回|APY|财富|持仓|收益|理财)", "充值理财"),
    # ... more UVISA-specific patterns
]
```

Both anti-patterns require code changes when projects evolve. User correction (2026-05-30): "为什么是硬编码？寻找相关论点以及核心著作"

### Correct pattern: Config-driven via project profile

Read domain groups from project profile — zero hardcoded project knowledge in orchestrator code.

**Project profile structure (`~/.hermes/project-profiles/<project>.json`):**
```json
{
  "fullstack_domain_map": {
    "exchange": {"frontend": ["src/screens/exchange/"], "backend": ["api/.../ExchangeController.java"]},
    "notification": {"frontend": ["src/services/notification.service.ts"], "backend": ["api/.../NotificationController.java"]},
    ...
  },
  "domain_aliases": {
    "exchange": ["兑换", "汇率", "换汇"],
    "notification": ["通知", "消息", "站内信", "横幅", "全部已读"],
    "remit": ["汇款", "收款人", "跨境汇款"],
    "topup": ["转入", "充值", "境内转账"],
    "payout": ["转出", "提现", "网络费"],
    "wealth": ["财富", "理财", "赎回", "持仓", "申购", "收益"],
    "auth": ["登录", "注册", "验证码", "密码", "PWA", "安全区"],
    "wallet": ["资产", "钱包", "余额", "币种", "交易记录"],
    "kyc": ["KYC", "身份核验", "认证"],
    "mfa": ["GA", "二次验证", "MFA"],
    "admin": ["admin", "管理后台", "后台"]
  }
}
```

**Orchestrator logic (reads config, no project knowledge):**
```python
def _load_domain_groups_from_profile(task):
    """Load {keyword: domain} mapping from project profile."""
    profile = load_project_profile(task.project)
    domain_aliases = profile.get("domain_aliases", {})
    if domain_aliases:
        keyword_map = {}
        for domain, keywords in domain_aliases.items():
            keyword_map[domain.lower()] = domain.lower()
            for kw in keywords:
                keyword_map[kw.lower()] = domain.lower()
        return keyword_map
    # Fallback: use fullstack_domain_map keys directly
    domain_map = profile.get("fullstack_domain_map", {})
    return {k.lower(): k.lower() for k in domain_map if not k.startswith("_")}

def _extract_page_key_from_title(title, domains):
    """Match against domain keywords (longest match first), then fallback."""
    title_lower = title.lower()
    matched_domain, matched_len = None, 0
    for keyword, domain in domains.items():
        if keyword in title_lower and len(keyword) > matched_len:
            matched_domain, matched_len = domain, len(keyword)
    if matched_domain:
        return matched_domain
    # Fallback: extract first meaningful Chinese/English phrase
    stripped = re.sub(r"^(用户端[—\-—\s]*|admin[—\-—\s]*|(feat|fix|chore|refactor)[\s:：]+)", "", title).strip()
    if not stripped:
        return "通用"
    m = re.match(r"([\u4e00-\u9fff]{2,8})", stripped)
    if m: return m.group(1)
    m = re.match(r"([a-zA-Z][a-zA-Z0-9_-]+(?:\s+[a-zA-Z][a-zA-Z0-9_-]+)?)", stripped)
    if m: return m.group(1)
    return "通用"

def _refine_boundary_with_page_key(task, boundary):
    """Refine ANY boundary using project profile config."""
    if _boundary_depth(boundary) >= 3:  # already refined
        return boundary
    domains = _load_domain_groups_from_profile(task)
    page_key = _extract_page_key_from_title(task.title, domains)
    return f"{boundary}:{page_key}"
```

**Why this is correct:**
- **Zero hardcoded project knowledge** in orchestrator/classifier code
- New projects just add `domain_aliases` to their profile — no code change
- `domain_aliases` maps Chinese keywords → English domain names (bridging the i18n gap)
- Longest-match-first prevents partial matches (e.g., "转入" matching before "转出跨境汇款")
- Depth >= 3 check replaces the old "ends with known page key" check — works for any project
- Fallback to title-based phrase extraction when no domain match found

### Integration Points

1. **`task_parallel_boundary_key(task)`** in `brain_task_orchestrator.py`:
   - After resolving explicit boundary, call `_refine_boundary_with_page_key(task, explicit)`
   - This is the canonical key used by dispatch, claim, and conflict detection

2. **`compute_boundary_key(task: dict)`** in `task_classifier.py`:
   - Must replicate the same logic using dict access (`task.get('title')`, `task.get('mission_title')`)
   - Add a dict-based `_refine_boundary_with_page_key_dict()` variant
   - Both files must produce identical keys for the same task

3. **Dynamic-N group counting** in `brain_task_orchestrator.py`:
   - ALL places that count groups must use `task_parallel_boundary_key(t)` instead of raw frontmatter
   - Search for `conflict_group` or `parallel_boundary` in group-counting loops
   - Typical locations: `command_parallel_claim_and_handoff()`, dynamic-N state update

### Zero-Migration Guarantee

- Frontmatter `parallel_boundary` stays as-is
- Refinement is purely computed at read time
- Rollback = delete the refinement function

### Effect on Dynamic N

```
Before: 1 group  → N = min(ceil(27/7), 1, 3) = 1
After:  8 groups → N = min(ceil(27/7), 8, 3) = 3
```

### Adding Domain Aliases for a New Project

1. Add `domain_aliases` to the project profile (`~/.hermes/project-profiles/<project>.json`)
2. Map each domain name to its Chinese keyword variants (or other natural-language identifiers)
3. Keywords are matched case-insensitively, longest-match-first
4. If no `domain_aliases` exists, falls back to `fullstack_domain_map` keys (English domain names only)
5. **No code change needed** — orchestrator and classifier read from profile at runtime

### Dual-Path Pitfall

The orchestrator uses `Task` objects (attribute access: `task.title`, `task.fm`).
The classifier uses plain dicts (key access: `task.get('title')`).

Both need their own refinement function. Keep them in sync — if one changes, the other must too. A future refactor could extract a shared utility, but the current approach avoids circular imports between the two scripts.

### Dynamic-N State Pitfall

When the refinement logic changes (e.g., from hardcoded prefixes to content-based), existing `dynamic_n_state.json` may have stale `current_n` from the old grouping. The smoothing mechanism (`SMOOTHING_CYCLES=2`) means the new N won't take effect until 2 consecutive cycles report it. To apply immediately, reset the state file:

```python
import json
from datetime import datetime, timezone
state = {
    'current_n': <new_n>,
    'candidate_n': None,
    'candidate_count': 0,
    'history': [{'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                 'dispatchable': N, 'groups': M, 'raw_n': R, 'applied_n': R}]
}
with open('state/dynamic_n_state.json', 'w') as f:
    json.dump(state, f, indent=2)
```

Verify with `python3 scripts/agent_team_controller.py status --json` — `conflict_groups` should show page-level groups, not a single coarse group.
