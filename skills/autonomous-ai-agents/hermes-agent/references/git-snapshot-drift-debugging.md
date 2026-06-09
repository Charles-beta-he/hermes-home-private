# Staged vs worktree drift in local Hermes/vendor debugging

When a runtime or downstream task still reproduces a bug after the source file looks fixed, verify which snapshot the consumer is actually reading.

Checklist:
1. Compare all three views, not just the worktree:
   - worktree: `python3 - <<'PY' ... Path('run_agent.py').read_text() ... PY` or plain file read
   - index/staged: `git -C /path/to/repo show :run_agent.py`
   - HEAD: `git -C /path/to/repo show HEAD:run_agent.py`
2. If the worktree is fixed but the index still has the bad ordering/content, re-stage the corrected file before trusting downstream runs.
3. When the bug is a local rewrite/regression around prompt assembly, search exact symbol positions across snapshots (example: `context_parts: List[str] = []` vs earlier `context_parts.append(...)`).
4. Validate syntax after repair (`python3 -m py_compile run_agent.py`) so the restage does not promote a new syntax error.

Why this matters:
- Some consumers read the staged snapshot, generated patch bundle, or another git-derived artifact instead of the current worktree.
- This creates a misleading state where "the file looks fixed" but the task chain still sees the old bug.

Example from Hermes:
- `context_parts.append(_filtered)` and env-hint appends appeared before `context_parts: List[str] = []` in the staged snapshot, which preserved an `UnboundLocalError`, while the worktree already had the initialization moved earlier.
