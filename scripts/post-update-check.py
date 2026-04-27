#!/usr/bin/env python3
"""
Hermes post-update self-check: detect if vendor-code patches have been
overwritten by `hermes update`, re-apply if needed, report fixed-by-upstream.

Usage:
    python3 ~/.hermes/scripts/post-update-check.py [--fix]

Without --fix: dry-run mode — only report what needs fixing.
With    --fix: apply patches when needed.
"""

import re
import os
import sys
import subprocess

HERMES_ROOT = os.path.expanduser("~/.hermes/hermes-agent")
CHECKS = []

def register(name, file_rel, pattern_needle, fix_desc, fix_func=None):
    """Register a check. fix_func(path) applies the fix, returns bool."""
    CHECKS.append({
        "name": name,
        "path": os.path.join(HERMES_ROOT, file_rel),
        "needle": pattern_needle,
        "fix_desc": fix_desc,
        "fix_func": fix_func,
    })


# ── Check 1: chat_completions.py truthiness bug ─────────────────
def _fix_chat_completions_truthiness(path):
    with open(path, "r") as f:
        content = f.read()
    old = "if reasoning_content:\n            provider_data[\"reasoning_content\"] = reasoning_content"
    new = "if reasoning_content is not None:\n            provider_data[\"reasoning_content\"] = reasoning_content"
    if old in content:
        content = content.replace(old, new)
        with open(path, "w") as f:
            f.write(content)
        return True
    return False

register(
    "chat_completions_truthiness",
    "agent/transports/chat_completions.py",
    r'if reasoning_content:\s+provider_data\["reasoning_content"\]',
    "if reasoning_content: → if reasoning_content is not None: (empty string not stored)",
    _fix_chat_completions_truthiness,
)


# ── Check 2: _copy_reasoning_content_for_api step ordering ──────
def _fix_step_ordering(path):
    """Reorder _copy_reasoning_content_for_api so reasoning promotion
    happens BEFORE the DeepSeek/Kimi empty-string fallback.

    Strategy: swap two adjacent blocks in the method body using
    direct text replacement. Each block is identified by its comment header.
    """
    with open(path, "r") as f:
        content = f.read()

    # Detect order via comment markers
    has_promote_as_step2 = "# 2. Healthy session: promote 'reasoning'" in content
    has_deepseek_as_step3 = "# 3. DeepSeek / Kimi thinking mode: tool-call" in content
    has_deepseek_as_step2 = "# 2. DeepSeek / Kimi thinking mode: tool-call" in content
    has_promote_as_step3 = "# 3. Healthy session: promote 'reasoning'" in content

    if has_promote_as_step2 and has_deepseek_as_step3:
        return False  # Already correct order

    if has_deepseek_as_step2 and has_promote_as_step3:
        # Swap: move the promote block before the needs_empty_reasoning block
        # Use the exact text replacement
        old_order_block = """        # 2. DeepSeek / Kimi thinking mode: tool-call turns that lack
        # reasoning_content are "poisoned history" — a prior provider (MiniMax,
        # etc.) left them empty. DeepSeek returns HTTP 400 if reasoning_content
        # is absent on replay; inject "" to satisfy the provider's requirement
        # without forwarding any cross-provider reasoning content.
        needs_empty_reasoning = (
            source_msg.get("tool_calls")
            and (
                self._needs_kimi_tool_reasoning()
                or self._needs_deepseek_tool_reasoning()
            )
        )
        if needs_empty_reasoning:
            api_msg["reasoning_content"] = ""
            return

        # 3. Healthy session: promote 'reasoning' field to 'reasoning_content'
        # for providers that use the internal 'reasoning' key.
        normalized_reasoning = source_msg.get("reasoning")
        if isinstance(normalized_reasoning, str) and normalized_reasoning:
            api_msg["reasoning_content"] = normalized_reasoning
            return"""

        new_order_block = """        # 2. Healthy session: promote 'reasoning' field to 'reasoning_content'
        # for providers that use the internal 'reasoning' key.
        normalized_reasoning = source_msg.get("reasoning")
        if isinstance(normalized_reasoning, str) and normalized_reasoning:
            api_msg["reasoning_content"] = normalized_reasoning
            return

        # 3. DeepSeek / Kimi thinking mode: tool-call turns that lack
        # reasoning_content are "poisoned history" — a prior provider (MiniMax,
        # etc.) left them empty. DeepSeek returns HTTP 400 if reasoning_content
        # is absent on replay; inject "" to satisfy the provider's requirement
        # without forwarding any cross-provider reasoning content.
        needs_empty_reasoning = (
            source_msg.get("tool_calls")
            and (
                self._needs_kimi_tool_reasoning()
                or self._needs_deepseek_tool_reasoning()
            )
        )
        if needs_empty_reasoning:
            api_msg["reasoning_content"] = ""
            return"""

        if old_order_block in content:
            content = content.replace(old_order_block, new_order_block)
            with open(path, "w") as f:
                f.write(content)
            return True

    return False


register(
    "reasoning_content_step_ordering",
    "run_agent.py",
    r'# 2\. DeepSeek / Kimi thinking mode.*?needs_empty_reasoning',
    "Reposition 'reasoning' promotion before DeepSeek empty-string fallback",
    _fix_step_ordering,
)


# ── Check 3: remove_duplicate_project_desc (memory) ─────────────
MEMORY_FILE = os.path.expanduser("~/.hermes/memories/MEMORY.md")
def check_memory_ghosts():
    """Check MEMORY.md for known ghost patterns. Not auto-fixed."""
    if not os.path.exists(MEMORY_FILE):
        return "MISSING"
    with open(MEMORY_FILE) as f:
        content = f.read()
    ghosts = []
    if "v1.4.8" in content:
        ghosts.append("version number (v1.4.8)")
    if "动效系统优化" in content and "无改进" in content:
        ghosts.append("completed animation optimization summary")
    if "Discover 页面" in content and "已上线" in content:
        ghosts.append("past-tense 'Discover page launched'")
    if ghosts:
        return f"GHOSTS DETECTED: {', '.join(ghosts)}"
    return "OK"
register(
    "memory_ghosts",
    ".",  # dummy
    None,
    "Check MEMORY.md for past-tense ghost entries (manual fix)",
)


# ── Check 5: skill tracking (Axis 5) ──────────────────────────
USAGE_FILE = os.path.expanduser("~/.hermes/skills/steward/skill_usage.json")
TRACKER_PLUGIN_DIR = os.path.expanduser("~/.hermes/plugins/skill-tracker")

def check_skill_tracking():
    """Check if skill tracking is operational."""
    plugin_ok = os.path.exists(os.path.join(TRACKER_PLUGIN_DIR, "__init__.py"))
    usage_ok = os.path.exists(USAGE_FILE)
    if not plugin_ok:
        return "NO_PLUGIN"
    if not usage_ok:
        return "INSTALLED_NO_DATA_YET"
    try:
        with open(USAGE_FILE) as f:
            data = json.load(f)
        total_loads = sum(len(v) for v in data.values())
        skills_loaded = len(data)
        return f"OK ({skills_loaded} skills, ~{total_loads} loads)"
    except Exception as e:
        return f"ERROR: {e}"

register(
    "skill_tracking",
    ".",  # dummy
    None,
    "Check skill usage tracking plugin + data",
)
STEWARD_STATE = os.path.expanduser("~/.hermes/skills/steward/state.json")

def check_steward_liveness():
    import json
    if not os.path.exists(STEWARD_STATE):
        return "MISSING"
    try:
        with open(STEWARD_STATE) as f:
            state = json.load(f)
        triggers = state.get("rule_triggers", {})
        active = {k for k, v in triggers.items() if v and v > 0}
        if not active:
            return "DORMANT (0 rules triggered)"
        return f"OK ({len(active)} rules active: {active})"
    except Exception as e:
        return f"ERROR: {e}"
register(
    "steward_liveness",
    ".",  # dummy
    None,
    "Check steward rule_triggers are non-zero (needs cron history)",
)


# ── Check 7: skill quality (test-prompts coverage) ────────────
SKILLS_DIR = os.path.expanduser("~/.hermes/skills")

def check_skill_quality():
    """Check which skills are missing test-prompts.json."""
    if not os.path.exists(SKILLS_DIR):
        return "MISSING"
    total = 0
    missing_tests = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        if "SKILL.md" in files:
            total += 1
            # Check if it's an alias
            sk_path = os.path.join(root, "SKILL.md")
            try:
                with open(sk_path) as f:
                    first_lines = f.read(200)
                if "alias: true" in first_lines:
                    continue  # skip aliases
            except Exception:
                pass
            if "test-prompts.json" not in files:
                rel = os.path.relpath(root, SKILLS_DIR)
                missing_tests.append(rel)
    if not missing_tests:
        return f"OK ({total} skills, all have tests)"
    return f"MISSING ({len(missing_tests)}/{total} no tests: {', '.join(missing_tests[:5])})"

register(
    "skill_quality",
    ".",
    None,
    "Check which skills lack test-prompts.json",
)


# ═══════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════

def main():
    apply_fixes = "--fix" in sys.argv

    print("═" * 56)
    print("  Hermes Post-Update Self-Check")
    print(f"  Hermes root: {HERMES_ROOT}")
    print(f"  Mode: {'FIX' if apply_fixes else 'DRY RUN'} (pass --fix to apply)")
    print("═" * 56)
    print()

    statuses = []

    for check in CHECKS:
        name = check["name"]
        path = check["path"]
        needle = check["needle"]
        fix_desc = check["fix_desc"]
        fix_func = check["fix_func"]

        print(f"  [{name}]")

            # Memory & steward checks use their own logic
        if needle is None:
            if "memory" in name:
                result = check_memory_ghosts()
            elif "steward" in name:
                result = check_steward_liveness()
            elif "skill_tracking" in name:
                result = check_skill_tracking()
            elif "skill_quality" in name:
                result = check_skill_quality()
            else:
                result = ""
            if result == "OK":
                print(f"    ✅ {result}")
                statuses.append((name, "OK"))
            elif result and result.startswith("GHOSTS"):
                print(f"    ⚠️  {result}")
                statuses.append((name, "MANUAL"))
            elif result and result.startswith("DORMANT"):
                print(f"    💤 {result}")
                statuses.append((name, "DORMANT"))
            elif result and result.startswith("INSTALLED"):
                print(f"    📦 {result}")
                statuses.append((name, result))
            else:
                print(f"    ⚠️  {result}")
                statuses.append((name, result))
            continue

        # File-based checks
        if not os.path.exists(path):
            print(f"    ⚠️  FILE MISSING: {path}")
            statuses.append((name, "MISSING"))
            continue

        with open(path) as f:
            content = f.read()

        # Check if the bug pattern is present
        if re.search(needle, content):
            # Bug still present
            if fix_func and apply_fixes:
                if fix_func(path):
                    print(f"    🔧 FIXED: {fix_desc}")
                    statuses.append((name, "FIXED"))
                else:
                    print(f"    ❌ FIX FAILED: {fix_desc}")
                    statuses.append((name, "FIX_FAILED"))
            elif fix_func:
                print(f"    ⚠️  NEEDS FIX: {fix_desc}")
                print(f"       Run with --fix to apply")
                statuses.append((name, "NEEDS_FIX"))
            else:
                print(f"    ⚠️  BUG PRESENT (no auto-fix): {fix_desc}")
                statuses.append((name, "MANUAL"))
        else:
            # Bug not found — already fixed or doesn't apply
            print(f"    ✅ No issue detected (fixed by upstream or not applicable)")
            statuses.append((name, "OK"))

    print()
    print("═" * 56)
    print("  Summary")
    print("═" * 56)

    ok_count = sum(1 for _, s in statuses if s == "OK")
    fix_count = sum(1 for _, s in statuses if "FIX" in s)
    warn_count = sum(1 for _, s in statuses if s in ("NEEDS_FIX", "MANUAL", "DORMANT", "GHOSTS", "MISSING"))

    for name, status in statuses:
        icon = {"OK": "✅", "FIXED": "🔧", "NEEDS_FIX": "⚠️", "MANUAL": "👤",
                "DORMANT": "💤", "FIX_FAILED": "❌", "MISSING": "⚠️",
                "INSTALLED_NO_DATA_YET": "📦"}.get(status, "❓")
        print(f"  {icon} {name}: {status}")

    print()
    print(f"  {ok_count} OK  |  {fix_count} fixed  |  {warn_count} need attention")
    print()


if __name__ == "__main__":
    main()
