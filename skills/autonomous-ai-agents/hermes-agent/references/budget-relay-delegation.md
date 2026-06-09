# Budget relay delegation debugging

Use when Hermes Agent appears to have a budget-relay / continuation design on paper but complex delegated tasks still stop after budget exhaustion.

Key lessons
- Check both worktree and index/staged snapshots. A local fix in `run_agent.py` can exist in the worktree while the staged/index snapshot still contains the broken version. If task pipelines read staged content, restage the fixed file before concluding the feature is still broken.
- For relay-style features, inspect the real execution path, not just the top-level CLI wiring. In Hermes Agent, `cli.py` can configure the parent `AIAgent`, but delegated work may execute in child agents created by `tools/delegate_tool.py`.
- When a parent `AIAgent` has runtime flags for continuation behavior, verify `_build_child_agent(...)` explicitly propagates them. Constructor defaults on the child can silently disable the feature.

Concrete evidence pattern from this session
- `run_agent.py` already contained `IterationBudget`, `ContinuationPacket`, and auto-relay-on-budget-exhaustion logic.
- `cli.py` already copied `delegation.auto_relay` and `delegation.max_relay_count` onto the top-level agent.
- The missing link was child-agent inheritance in `tools/delegate_tool.py`: delegated subagents were created without copying `auto_relay_enabled` and `max_relay_count` from the parent agent.
- Fix pattern: after `child = AIAgent(...)`, assign `child.auto_relay_enabled` and `child.max_relay_count` from `parent_agent` with safe fallback to child defaults.

Recommended verification
1. Compare worktree vs index when behavior differs from source inspection.
2. Add a focused unit test around `_build_child_agent(...)` asserting relay-related parent settings propagate to the child.
3. Run syntax verification and the targeted delegate-tool test subset after patching.
