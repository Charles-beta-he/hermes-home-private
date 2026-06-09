# Auto-Relay on Budget / Tool-Iteration Exhaustion

Use this reference when Hermes reaches the tool-calling / max-iteration limit and the user expected the conversation to continue asynchronously instead of stopping with a partial summary.

## Durable lesson

Do not key auto-relay only on the literal string `budget_exhausted`. In real conversation-loop exits, Hermes may record max-tool exhaustion as either:

- `budget_exhausted`
- `max_iterations_reached(...)`

Both must be treated as relay-eligible exit reasons when the relay feature is enabled and a final summary exists.

## Current implementation shape

Core locations:

- `agent/agent_init.py`
  - initializes `auto_relay_enabled`
  - initializes `max_relay_count`
  - initializes `_relay_count`
- `agent/conversation_loop.py`
  - owns helper methods such as `_is_auto_relay_exit_reason`, `_should_auto_relay`, `_relay_packet_dir`, `_write_auto_relay_packet`, and `_try_auto_relay`
  - detects relay-eligible terminal states after the normal max-iteration / budget-exhaustion final response path
  - writes a relay packet
  - resets the iteration budget
  - constructs a relay prompt
  - recursively calls `run_conversation(...)` to continue the task
  - passes `persist_user_message=relay_prompt` for the synthetic relay turn; do not pass boolean `True` because the parameter stores a clean transcript string
- `tests/run_agent/test_auto_relay_continuation.py`
  - regression coverage for exit-reason recognition, relay gating, packet write behavior, and the successor-turn state transition

## Trigger conditions

All should be true:

1. The exit reason is relay-eligible:
   - exact `budget_exhausted`, or
   - prefix/pattern `max_iterations_reached(...)`
2. `auto_relay_enabled` is true.
3. `_relay_count < max_relay_count`.
4. A non-empty final summary / final response is available to seed the next turn.

## Execution flow

1. Normal conversation loop reaches the tool/iteration cap.
2. Hermes obtains the usual final summary for the exhausted turn.
3. Relay guard checks `_should_auto_relay(exit_reason, final_response)`.
4. A JSON relay packet is written under:
   - `~/.hermes/state/relay-packets/`
5. The current `iteration_budget` is reset to a fresh budget.
6. Hermes injects an auto-relay user prompt that includes:
   - relay index / max relay count
   - prior exit reason
   - prior summary
   - instruction to continue without repeating completed work
7. `run_conversation(...)` is called recursively.
8. The relay result is returned or merged with metadata such as:
   - `triggered`
   - `relay_index`
   - `packet_path`
   - `parent_turn_exit_reason`

## Config

Keep this configuration-driven and bounded:

```yaml
delegation:
  auto_relay: true
  max_relay_count: 3
```

Default-safe behavior: enabled by default is acceptable only when max relay count is bounded. Avoid unbounded recursion.

## Verification checklist

Run focused tests first:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python -m pytest tests/run_agent/test_auto_relay_continuation.py -q -o addopts=
python3 -m py_compile agent/conversation_loop.py agent/agent_init.py
```

Then run a real smoke test with an intentionally low max-iteration/tool budget so the loop hits exhaustion quickly and must auto-relay. Verify:

- a packet appears in `~/.hermes/state/relay-packets/`
- result metadata shows relay was triggered
- the successor prompt includes the previous summary
- work continues instead of ending with only a max-iterations summary

## Pitfalls

- `max_iterations_reached(...)` is a real-world exit reason; missing it makes relay appear configured but inactive.
- Do not rely on config names alone. Verify the actual conversation-loop terminal path and result metadata.
- Recursive relay grows stack depth; keep `max_relay_count <= 3` unless there is a deliberate stress-test plan.
- Relay continues the same task; it is not the same mechanism as background process notification, cron delivery, or background memory/skill review.
- If the auto-relay fix is present on disk but live CLI behavior still looks stale, check the Hermes process start time (`ps ... hermes`) against the fixing commit time; long-running CLI/gateway processes may need restart to load patched Python modules.
- If a user reports “after the conversation ended, async work did not continue,” classify the mechanism first: auto-relay, background process, cron, taskpool autorun, or bg-review. The debug path differs for each.
