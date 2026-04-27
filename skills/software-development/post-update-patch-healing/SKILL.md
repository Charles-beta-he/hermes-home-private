---
name: post-update-patch-healing
description: "Create self-healing patches that survive `hermes update` (or any git-pull-based update). When a vendor-code fix would be overwritten by `git pull`, create a standalone checker script outside the repo that detects regression patterns and re-applies fixes. Three-tier approach: Level 0 (user data, permanent) → Level 1 (standalone checker, update-safe) → Level 2 (vendor patches, updated-by-checker)."
---

# Post-Update Patch Healing

> **Problem**: `hermes update` runs `git pull` on the hermes-agent repo. Any local edits to `run_agent.py`, `cli.py`, `stream_consumer.py`, `chat_completions.py`, `types.py` etc. are **overwritten**.

> **Pattern**: Create a standalone script at `~/.hermes/scripts/` that detects known bug patterns in vendor files and re-applies fixes when needed. This script survives updates because it's outside the git repo.

## Three-Tier Architecture

```
Tier 0 — User Data (permanent, never overwritten)
  ├── ~/.hermes/memories/MEMORY.md        ghost entry cleanup
  ├── ~/.hermes/skills/                    skill files
  ├── ~/.hermes/scripts/                   custom scripts
  └── ~/.hermes/config.yaml                configuration
  
Tier 1 — Checker Script (update-safe, outside git)
  ├── ~/.hermes/scripts/post-update-check.py
  │   ├── Detects known bug patterns in vendor files
  │   ├── Re-applies patches with --fix mode
  │   └── Reports "already fixed by upstream" when applicable
  └── Auto-triggered by post-merge git hook
  
Tier 1.5 — Hermes Plugin (update-safe, native lifecycle hooks)
  ├── ~/.hermes/plugins/<name>/plugin.yaml      manifest
  ├── ~/.hermes/plugins/<name>/__init__.py       register() + hooks
  └── Survives update natively (outside git, loaded by Hermes at startup)

Tier 2 — Vendor Patches (overwritten by git pull)
  ├── run_agent.py                         step ordering fix
  ├── chat_completions.py                  truthiness fix
  └── stream_consumer.py / cli.py          think-tag state machine
```

> **Key insight from real usage**: Tier 1.5 (plugins) is strictly better than Tier 1+2 for most use cases. Prefer plugin hooks over vendor patches whenever possible.

## Git Post-Merge Hook Auto-Trigger

After `hermes update` (i.e., `git pull`), the post-merge hook auto-runs the checker:

```bash
# ~/.hermes/hermes-agent/.git/hooks/post-merge
#!/bin/sh
if [ "$1" != "merge" ] && [ "$1" != "squash" ]; then
    exit 0
fi
CHECKER="$HOME/.hermes/scripts/post-update-check.py"
if [ -f "$CHECKER" ]; then
    echo ""
    echo "⚕ Running post-update health check..."
    python3 "$CHECKER" --fix
    echo ""
fi
```

**Why this is safe**: `.git/hooks/` is not tracked by git — `git pull` never overwrites it. The hook survives updates indefinitely.

## Plugin Hooks Available for Self-Healing

Hermes exposes these hooks via `~/.hermes/plugins/<name>/`:

| Hook | Use Case | Example |
|------|----------|---------|
| `pre_tool_call` | Validate/skip tool calls before execution | Block dangerous file writes |
| `post_tool_call` | Observe tool results (observational only) | Skill usage tracking |
| `transform_tool_result` | Rewrite tool output before it enters context | Strip sensitive data |
| `pre_llm_call` | Inject context into user message before API call | Git branch info, timing data |
| `post_llm_call` | Observe final LLM response | WIP archive, logging |
| `pre_api_request` | Inject/modify API kwargs | Dynamic reasoning config |
| `on_session_start` | Initialize per-session state | Load tracking data |
| `on_session_end` | Flush/persist state | Write usage data to disk |

## How to Build a Post-Update Checker

### Step 1: Identify the 3 States

Every fix falls into one of these states after `git pull`:

| State | Meaning | Action |
|-------|---------|--------|
| **NEEDS_FIX** | Bug pattern present in vendor code | Apply patch |
| **OK** | Bug already fixed by upstream | Report "no action needed" |
| **UPSTREAM_CHANGED** | Upstream changed code in same area | Manual review needed |

### Step 2: Design the Check

Each check needs three things:

```python
# Pattern to detect (regex on file content)
needle = r'if reasoning_content:\s+provider_data\["reasoning_content"\]'

# Fix description (displayed to user)
fix_desc = "if reasoning_content: → if reasoning_content is not None:"

# Fix function
def fix_func(path):
    # Direct string replacement
    old = "if reasoning_content:"
    new = "if reasoning_content is not None:"
    with open(path) as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(path, 'w') as f:
            f.write(content)
        return True
    return False
```

### Step 3: Use Comment Markers for Precise Detection

Vendor code changes frequently. Use **code comment headers** (not line numbers) to detect whether a fix is needed:

```python
# DETECTION: check for specific comment markers
has_bug_pattern = "# 2. DeepSeek / Kimi thinking mode: tool-call turns" in content
has_fix_pattern = "# 2. Healthy session: promote 'reasoning' field" in content

if has_bug_pattern:
    # Old (broken) order detected → apply swap
    apply_swap()
elif has_fix_pattern:
    # New (correct) order detected → skip
    pass
```

### Step 4: Structured Output

The checker should produce a machine-readable table:

```python
for name, status in results:
    icon = {"OK": "✅", "FIXED": "🔧", "NEEDS_FIX": "⚠️",
            "MANUAL": "👤", "DORMANT": "💤", "FIX_FAILED": "❌"}
    print(f"  {icon} {name}: {status}")
```

## Decision Framework: Plan A vs Plan B

Before patching vendor code, evaluate two approaches:

```
Plan A: Deep Fix (vendor code + post-update-check protection)
  ───────────────────────────────────────────────────────
  适合: 修复需要改核心逻辑，不容易从插件层实现
  方法: 直接改 hermes-agent/ 文件 + post-update-check 自动重打
  保护: post-merge git hook 自动运行 --fix
  风险: upstream 重构代码后 patch 可能冲突

Plan B: Zero Vendor Intrusion (plugin + config + skill only)
  ───────────────────────────────────────────────────────
  适合: 功能可以完全通过 hooks/config/SKILL.md 实现
  方法: ~/.hermes/plugins/<name>/ + config.yaml + skills/
  保护: 不需要 — 全部在 git repo 外
  风险: 部分修复是"弥补"而非"根治"

决策树:
  能否用插件 hook 实现？          → Yes → Plan B
  是否只需改 config/yaml？        → Yes → Plan B
  是否核心逻辑层 bug？            → Yes → Plan A
  修正后 upstream 可能合并吗？    → Yes → Plan A (+ 提 PR)
```

## Multi-Loop Convergence Pattern

When fixing multiple issues in one session, use an iterative convergence loop:

```
Iteration 1:  fix issue A  →  run checker  →  A OK, B discovered
Iteration 2:  fix issue B  →  run checker  →  A+B OK, C discovered
...
Iteration N:  fix issue N  →  run checker  →  ALL OK  →  DONE
```

**Convergence condition:** All checks report OK or explicitly time-dependent (💤/📦).

```python
# In practice, structure as:
todo_list = [
    "config changes (persistent)",
    "plugins (update-safe)",
    "vendor patches (post-update-check protected)",
    "skills + test-prompts",
]

while not all_done:
    pick_next_todo()
    execute_fix()
    run_self_check()
    if no_new_issues:
        mark_done()
    
# Stop when:
#   - All actionable items are OK or 💤/📦
#   - Remaining items are time-dependent (will self-resolve)
```

## Time-Dependent Metrics

Some checks can never report OK on day 1:

| Metric | Why | When it resolves |
|--------|-----|-----------------|
| Steward rule liveness (💤 DORMANT) | Rules need cron history | ~7 days of nightly runs |
| Skill usage tracking (📦 INSTALLED_NO_DATA_YET) | No data until next session restart | After 1+ agent session |
| Rule triggers (0 active) | No stale skills to flag yet | When a skill hits 90d without tests |

Label these explicitly so they don't block convergence:

```python
elif result.startswith("DORMANT"):
    print(f"    💤 {result}")
elif result.startswith("INSTALLED"):
    print(f"    📦 {result}")
```

## Cross-Session Detection Pattern

After converging a loop, always check if the **system itself** has blind spots:

```python
# After all existing checks pass, ask:
# 1. "Are there dimensions of quality my current checks miss?"
# 2. "Do I need a new check for something that happened during the fix?"
# 3. "Is the steward detecting everything the ecosystem needs?"
```

## Content Overlap False-Positive Mitigation

The content_overlap detector went through **two iterations** before producing useful results:

```
Iteration 1: Full body token overlap -> 253 false-positive pairs
             Root cause: common words dominate Jaccard
             Fix: added STOPWORDS set with ~80 English + Chinese words

Iteration 2: Description-only overlap -> 255 pairs (still false)
             Root cause: category stubs all have "X workflow skill" pattern
             Fix: skip skills with <200 body words (filters out stubs)

Iteration 3: Body words >200, STOPWORDS filtered -> 2 real pairs
             semantic-release vs cloudflare-pages (0.41)
             axolotl vs unsloth (0.39)
```

Key lesson: Start with strict filters. Only loosen if real overlaps are missed. False negatives beat false positives.

## Pitfalls

1. **Don't use line numbers**: Line numbers change every time the file is edited. Use unique comment strings or code patterns.

2. **Don't use complex indentation parsing**: Multi-line expressions (e.g. `needs_empty_reasoning = (\n    source_msg.get(...)`) are fragile. Use exact string replacement of the full block instead.

3. **Auto-fix must be opt-in**: Default to dry-run. Require `--fix` flag to apply changes.

4. **Report upstream fixes**: When upstream has already fixed something, say "no longer needed" explicitly.

5. **Standalone script, not plugin**: Put the checker at `~/.hermes/scripts/` (outside the git repo).

6. **Don't use truthiness checks in normalize_response**: `if reasoning_content:` silently drops empty strings `""`. Use `if reasoning_content is not None:` instead.

7. **Regex needle mismatch causes false OK**: Test each needle against a known-broken file copy. Verify the needle does NOT match after the fix is applied.

8. **Post-merge hook only runs on actual merges**: `git pull --rebase` won't trigger post-merge.

9. **Git hooks persist through updates**: `.git/hooks/` is not tracked by git. Post-merge hooks survive indefinitely.

## Plugin Example: Skill Usage Tracker

```yaml
# ~/.hermes/plugins/skill-tracker/plugin.yaml
name: skill-tracker
hooks:
  - post_tool_call
  - on_session_end
```

```python
# ~/.hermes/plugins/skill-tracker/__init__.py
import json, os, time
from pathlib import Path
USAGE_FILE = Path(os.path.expanduser("~/.hermes/skills/steward/skill_usage.json"))
def _on_post_tool_call(tool_name="", args=None, **kwargs):
    if tool_name == "skill_view" and args and args.get("name"):
        _record(args["name"])
def _on_session_end(**kwargs):
    _flush()
def register(ctx):
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_end", _on_session_end)
```

## Known Patches (as of Apr 2026)

| Fix | File | Detection Pattern |
|-----|------|-------------------|
| Truthiness for empty reasoning_content | `agent/transports/chat_completions.py` | `if reasoning_content:` before `provider_data\["reasoning_content"\]` |
| Step ordering in `_copy_reasoning_content_for_api` | `run_agent.py` | `# 2\. DeepSeek / Kimi thinking mode` before `needs_empty_reasoning` |
| MemoryManager provider registration rollback | `agent/memory_manager.py` | `self._providers.append(provider)` followed by bare `for schema in provider.get_tool_schemas()` without try/except |
| MCP call_tool asyncio timeout guard | `tools/mcp_tool.py` | `async def _call():` followed by bare `await server.session.call_tool(...)` without `asyncio.wait_for` |

## Related

- `systematic-debugging` — general debugging methodology
- `skill-ecosystem-diagnosis` — five hard problems diagnosis
- `skill-ecosystem-governance` — steward governance system
- `mcp/native-mcp` — MCP transport handling
