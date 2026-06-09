# Budget relay debugging in Hermes Agent

Durable lessons from implementing and verifying budget relay / continuation behavior.

## Failure pattern
A feature can look implemented in `run_agent.py` but still fail in real delegated task execution because the relay path spans:
- top-level CLI config (`delegation.auto_relay`, `delegation.max_relay_count`)
- child-agent construction in `tools/delegate_tool.py`
- post-summary continuation logic in `run_agent.py`
- staged/index snapshots if downstream tooling reads git index instead of worktree

## Verified pitfalls
1. `delegate_tool._build_child_agent()` must propagate relay settings from parent to child:
   - `child.auto_relay_enabled = parent.auto_relay_enabled`
   - `child.max_relay_count = parent.max_relay_count`
   Otherwise the parent advertises relay support but real delegated work never relays.

2. Auto-relay cannot key only on `turn_exit_reason == "budget_exhausted"`.
   Real runs often exit the main loop, request a summary, and end with
   `max_iterations_reached(...)`. Relay must treat both as continuation-worthy.

3. Preserve or normalize relay reason across the summary handoff.
   Summary generation can overwrite the raw budget-exhausted marker; verify the
   post-summary continuation gate still fires and `ContinuationPacket.reason`
   matches the actual exit class (`budget_exhausted` or `max_iterations`).

4. When local edits moved logic around, compare worktree and git index.
   A fixed worktree file can coexist with a broken staged snapshot, which matters
   if a task chain consumes staged diffs / index-based bundles.

## Verification recipe
- Run syntax check on `run_agent.py`, `tools/delegate_tool.py`, and any new tests.
- Add / run a focused `run_agent` test that proves this chain:
  1. first call uses a tool and exhausts iterations
  2. summary call returns progress text
  3. auto-relay fires with fresh budget
  4. relay packet is written
  5. final response comes from the relay turn
- Add / run a focused `delegate_tool` test that proves child agents inherit relay settings.
- If the symptom only appears in a task pipeline, re-stage the corrected files and verify the staged snapshot matches the worktree before concluding the fix landed.