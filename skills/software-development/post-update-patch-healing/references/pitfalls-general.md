# Pitfalls (General)

Extracted from `/Users/charles/.hermes/skills/software-development/post-update-patch-healing/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Pitfalls (General)

1. **Don't use line numbers**: Line numbers change every time the file is edited. Use unique comment strings or code patterns.

2. **Don't use complex indentation parsing**: Multi-line expressions (e.g. `needs_empty_reasoning = (\n    source_msg.get(...)`) are fragile. Use exact string replacement of the full block instead.

2b. **Don't use regex for multi-line indentation changes**: `re.sub()` with patterns spanning `async with X:\n    result = await ...` breaks indentation when the `async with` line is removed but the inner line retains its extra indent. The correct approach is **line-by-line processing**: scan for the lock line, skip it, and dedent the next line by the exact amount (typically 4 spaces). This was the root cause of 3 failed attempts in the 2026-05-12 MCP patch session — regex approach broke syntax, restore from backup, then line-by-line succeeded on first try.

3. **Auto-fix must be opt-in**: Default to dry-run. Require `--fix` flag to apply changes.

4. **Report upstream fixes**: When upstream has already fixed something, say "no longer needed" explicitly.

5. **Standalone script, not plugin**: Put the checker at `~/.hermes/scripts/` (outside the git repo).

6. **Don't use truthiness checks in normalize_response**: `if reasoning_content:` silently drops empty strings `""`. Use `if reasoning_content is not None:` instead.

7. **Regex needle mismatch causes false OK**: Test each needle against a known-broken file copy. Verify the needle does NOT match after the fix is applied.

8. **Post-merge hook only runs on actual merges**: `git pull --rebase` won't trigger post-merge.

9. **Git hooks persist through updates**: `.git/hooks/` is not tracked by git. Post-merge hooks survive indefinitely.

10. **Use venv python for py_compile, not system python**: System `python3` may have different build flags or PATH issues. Always use `./venv/bin/python -m py_compile` (or `.venv/`). In the 2026-05-12 session, system python3 hit `SyntaxError: invalid syntax` on `match` statements (even though both reported 3.11), while venv python correctly showed the actual indentation error. Pattern: `cd ~/.hermes/hermes-agent && ./venv/bin/python -m py_compile tools/mcp_tool.py`.

11. **Always backup before patching**: `cp path/to/file path/to/file.bak.$(date +%Y%m%d%H%M%S)`. When a multi-location patch breaks syntax, restoring from backup is faster than trying to reverse individual edits. The 2026-05-12 session needed 3 restores from backup before finding the correct patching approach.

12. **Run MCP-specific tests after patching mcp_tool.py**: `./venv/bin/python -m pytest tests/tools/test_mcp_tool.py tests/tools/test_mcp_stability.py -x -q` — the 199-test suite covers all 5 RPC operations, timeout behavior, and interrupt handling. Two RuntimeWarning about unawaited coroutines in interrupt-test scenarios are expected (not regressions).

13. **Line-by-line processing template for indentation-sensitive patches**: When a patch removes a wrapping construct (like `async with X:`) and needs to dedent the inner line, use this pattern:
    ```python
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if stripped == "async with server._rpc_lock:" and i + 1 < len(lines):
            next_line = lines[i + 1]
            next_stripped = next_line.lstrip()
            if next_stripped.startswith("result = await server.session."):
                indent = line[:len(line) - len(stripped)]
                new_lines.append(indent + next_stripped)
                i += 2
                continue
        new_lines.append(line)
        i += 1
    content = '\n'.join(new_lines)
    ```

14. **Codex timeout hardening must cover both main and auxiliary paths**: If Codex/OAuth transport starts timing out, do not only increase a global timeout. Add provider/model-scoped circuit breaking, split HTTP timeouts, and close/evict poisoned cached clients on every timeout branch. The auxiliary foreground-deadline branch is easy to miss because it can set `timed_out=True` without raising the same exception path as API timeouts. See `references/codex-transport-hardening.md`.

15. **Certification manifest beats discussion optimism**: In multi-model verification after a self-update, a `discussion_result.json` approval is not sufficient if the manifest reports planner/fanout mismatch, parser failure, or `can_claim_complete_certification=false`. Report it as deterministic gates passing plus degraded/advisory model review; do not claim 4/4 certification.
