---
name: post-update-patch-healing
description: Use when you need to create self-healing patches that survive `hermes update` (or any git-pull-based update).
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - software
    - development
    - post
    - update
    - patch
    related_skills:
    - axolotl
    - claude-code
    - design
    - hermes-agent
    - loop
    - mcp
    - native-mcp
    - skill-ecosystem-diagnosis
---

# Post-Update Patch Healing

## When to Use

Use this skill when the request matches the `post-update-patch-healing` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Overview


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
# Git post-merge receives one argument: 0 for a normal merge/fast-forward,
# 1 for a squash merge. It is NOT the string "merge"/"squash".
# For `hermes update`/`git pull`, run on normal post-merge events.
if [ "${1:-0}" != "0" ] && [ "${1:-0}" != "1" ]; then
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

## Multi-Agent Design for Complex Patches

When a patch grows beyond a single-location regex fix (e.g., touches 6+ locations across a file), the standard post-update-check auto-fix approach breaks down. Use this workflow instead:

### When to Use

- Patch touches 3+ locations in the same file
- Patch requires architectural decisions (not just bug fixes)
- Patch needs to interact with upstream's own changes (e.g., upstream added a lock, local added a timeout)

### Workflow

1. **Analyze**: Identify all affected locations and their current state
2. **Consult**: Delegate design to Claude Code with full context (current code, upstream changes, design constraints)
3. **Review**: Claude Code produces a design document with exact diffs, risk assessment, and PR template
4. **Implement**: Apply changes using patch tool or execute_code
5. **Verify**: Claude Code reviews the implementation against the design
6. **Test**: Run pytest with isolated HERMES_HOME

### Example: MCP _mcp_rpc_call Architecture

Problem: Upstream added `server._rpc_lock`, local patch added `asyncio.wait_for`. Combined they created double timeout, double circuit breaker bump, and lock starvation.

Solution: Claude Code designed a `_mcp_rpc_call` helper that centralizes lock + timeout. The outer `_run_on_mcp_loop` timeout became a safety net (inner + 30s) with `future.cancel()` on expiry. Applied to all 5 MCP operations for consistency.

Key design principle: **Inner timeout = primary (clear error, circuit breaker). Outer timeout = safety net (catastrophic failures only).**

### Patch Complexity Classification

| Complexity | Auto-fix? | Approach |
|-----------|-----------|----------|
| 1 location, simple string replace | YES | post-update-check regex |
| 2-3 locations, pattern-based | MAYBE | post-update-check with careful regex |
| 4+ locations, architectural | NO | Separate apply script + checker detects absence |
| Cross-file, design decisions | NO | Multi-agent design → implement → verify |

For "NO" auto-fix: checker detects the OLD state (bare `await server.session.xxx`) and reports NEEDS_FIX. User re-applies from backup or runs a dedicated script.

## Pitfalls (General)

Detailed `Pitfalls (General)` guidance moved to `references/pitfalls-general.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
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

| Fix | File | Status | Detection Pattern |
|-----|------|--------|-------------------|
| Truthiness for empty reasoning_content | `agent/transports/chat_completions.py` | **ACTIVE** — regresses after upstream refactors | `if reasoning_content:` before `provider_data["reasoning_content"]` |
| Step ordering in `_copy_reasoning_content_for_api` | `run_agent.py` | **UPSTREAM SUPERSEDED** — upstream refactored reasoning handling with cross-provider leak blocking (ee1a07f9), our old patch no longer needed | `# 2. DeepSeek / Kimi thinking mode` before `needs_empty_reasoning` |
| MemoryManager provider registration rollback | `agent/memory_manager.py` | **ACTIVE + CHECKER-COVERED** | `self._providers.append(provider)` followed by bare `for schema in provider.get_tool_schemas()` without try/except rollback |
| MCP RPC timeout guard (all operations) | `tools/mcp_tool.py` | **ACTIVE + FULLY INTEGRATED** | `_mcp_rpc_call(server, coro, timeout)` helper present — centralizes `server._rpc_lock` + timeout across all 5 MCP operations (call_tool, list/read resources, list/get prompts). Commit f0e69bd5d (2026-05-12). Post-update-check now detects OLD state and reports NEEDS_FIX. Re-apply via `~/.hermes/scripts/apply-mcp-timeout-patch.py` (line-by-line processing, not regex). 199 tests pass. |
| Codex transport hardening | `agent/codex_circuit_breaker.py`, `agent/auxiliary_client.py`, `run_agent.py`, `hermes_cli/timeouts.py` | **ACTIVE — SHOULD BE CHECKER-COVERED** | File-backed provider/model-scoped circuit breaker, split Codex HTTP timeouts (`connect=30/read=600/write=60/pool=60`), and cached-client close/evict on all timeout paths. Reapply via dedicated script/patch under `~/.hermes/scripts/` and integrate into `post-update-check.py`. See `references/codex-transport-hardening.md`. |
| Context compressor anti-ghost rules | `agent/context_compressor.py` | **ACTIVE + CHECKER-COVERED** | Compaction prompt without `CRITICAL — ANTI-GHOST RULES` (stale counters, "This session..." carry-forward) |
| Prompt builder ghost prevention | `agent/prompt_builder.py` | **ACTIVE + CHECKER-COVERED** | MEMORY_GUIDANCE without "Will this fact still be true in 10 sessions?" guard |

> **2026-05-12 upgrade (0.11.0 → 0.13.0)**: `hermes update` triggered `pip install` upgrading hermes-agent + 7 new deps. Post-update-check found 6 issues: 4 auto-fixed (--fix), 2 needed manual work. MCP RPC timeout guard FIX_FAILED (expected — 6-location patch). Manual re-apply: 3 failed attempts using regex-based `re.sub()` (broke indentation each time), restored from backup each time, finally succeeded with line-by-line processing approach. Key new pitfall: regex for multi-line indentation changes is fundamentally fragile — use line-by-line processing (see pitfall 2b). Also discovered: system python3 vs venv python behave differently on `match` statements — always use venv python for py_compile (pitfall 10). 199 MCP tests passed. All 9 post-update checks green. Commit f0e69bd5d.
>
> **2026-04-29 upgrade (198 commits)**: Pre-upgrade analysis identified 10 overlapping files. Extended checker with 4 new checks (memory_manager rollback, prompt_builder ghost, context_compressor anti-ghost, mcp rpc timeout guard). Post-merge hook fixed (was comparing `$1` to wrong strings). `git stash pop` had "would be overwritten" trap — resolved by restoring checker-modified files to HEAD before popping. `tools/mcp_tool.py` conflict resolved via multi-agent design: Claude Code designed `_mcp_rpc_call` helper architecture (lock + wait_for centralized, safety-net outer timeout with future.cancel), Hermes implemented all 12 changes, Claude Code verified. 182 MCP tests passed post-implementation. Key insight: complex patches (6+ locations) can't be auto-fixed by checker — use checker to detect absence, separate apply script or manual re-apply.
>
> **2026-04-27 upgrade (280 commits)**: truthiness regressed after upstream refactor, auto-fixed by post-update-check --fix. step_ordering superseded by upstream's better implementation (cross-provider reasoning leak blocking + unconditional DeepSeek/Kimi padding). 4 new patches added.
>
> **Critical lesson**: Patches marked "UPSTREAM FIXED" can REGRESS on the next upgrade. Always run post-update-check after every `hermes update`, even if patches were previously confirmed fixed. The post-merge hook handles this automatically.

## Controlled Upgrade Workflow

Detailed `Controlled Upgrade Workflow` guidance moved to `references/controlled-upgrade-workflow.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Known Patches (as of Apr 2026)

- `systematic-debugging` — general debugging methodology
- `skill-ecosystem-diagnosis` — five hard problems diagnosis
- `skill-ecosystem-governance` — steward governance system
- `mcp/native-mcp` — MCP transport handling
- `claude-code` — delegating complex conflict resolution and architectural design

## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
- [ ] Reviewer calibration: findings include a severity or rubric boundary and cite evidence.
