# Background review / post-turn async debugging

Use this reference when a user reports that Hermes did not continue or did not do anything after a conversation ended.

## First split the meaning of "async after conversation"

Hermes has several different mechanisms that users may describe the same way:

1. Background process completion notifications
   - Tools/process path: `terminal(background=true)`, `notify_on_complete`, `tools/process_registry.py`, completion queue, TUI gateway notification poller.
   - Verify with `process list`, `process poll`, and scheduler/gateway logs.

2. Continuation / relay of the main task
   - Do not assume this exists just because config contains names such as `delegation.auto_relay`.
   - Search code for the actual runtime path (`ContinuationPacket`, relay count, spawn relay, budget relay) before claiming continuation behavior is wired.

3. Background memory/skill review
   - Code path: `agent/conversation_loop.py` computes memory/skill nudge triggers, then calls `agent._spawn_background_review(...)` after the final response.
   - `run_agent.py::_spawn_background_review` creates `threading.Thread(..., daemon=True, name="bg-review")`.
   - `agent/background_review.py` runs a forked `AIAgent` and only surfaces a visible summary if it successfully performs memory/skill actions.

## Trigger checklist for background memory/skill review

Memory review usually requires:
- `memory.nudge_interval > 0`
- `"memory" in agent.valid_tool_names`
- a non-empty `agent._memory_store`
- accumulated user turns reaching the nudge interval
- final response exists and the turn was not interrupted

Skill review usually requires:
- `skills.creation_nudge_interval > 0`
- accumulated tool iterations reaching the interval
- `"skill_manage" in agent.valid_tool_names`
- final response exists and the turn was not interrupted

Important: a single user turn below threshold should not fire review. This is expected behavior, not a failed async mechanism.

## Evidence to collect

Use logs instead of guessing:
- `thread=bg-review` proves the review thread started.
- A main turn ending immediately before `thread=bg-review` ties the review to the user turn.
- `conversation turn ... msg='Review the conversation above and update the skill library...'` proves the review agent began work.
- `tool skill_manage completed` proves it actually changed skill state.
- `Tool skill_manage returned error` plus repeated tool-loop warnings prove the review got stuck in tool misuse.
- Missing matching `agent_close` / `Turn ended` for a bg-review thread suggests it hung or was still running.

Useful targeted scans:

```bash
python3 - <<'PY'
from pathlib import Path
for p in [Path('~/.hermes/logs/agent.log').expanduser(), Path('~/.hermes/logs/errors.log').expanduser()]:
    print('---', p.name)
    for line in p.read_text(errors='ignore').splitlines():
        if 'bg-review' in line or 'Self-improvement review' in line or 'Background memory/skill review failed' in line:
            print(line[:1400])
PY
```

```bash
python3 - <<'PY'
from pathlib import Path
lines = Path('~/.hermes/logs/agent.log').expanduser().read_text(errors='ignore').splitlines()
for i, line in enumerate(lines):
    if 'thread=bg-review' in line:
        for x in lines[max(0, i-5): i+25]:
            print(x[:1400])
        print('---')
PY
```

## Common root cause pattern

If bg-review inherits the parent runtime and full conversation snapshot, it can become too expensive or slow:
- huge `history` and 100k+ input-token review requests
- parent model/provider is slow or quota-limited
- repeated skill/memory tool schema errors cause more model turns
- daemon thread has no obvious user-visible status, so it looks like nothing happened

The visible symptom is often: main turn ended, bg-review starts, but no `Self-improvement review: ...` appears because the callback only fires after successful memory/skill actions.

## Implemented hardening (2026-05-18)

Hermes now has first-class background-review resilience in `agent/background_review.py`:

1. Visible status for failures, not just success.
   - Successful memory/skill writes still emit `💾 Self-improvement review: ...`.
   - Tool failures, API exceptions, and timeout paths emit `⚠️ Self-improvement review failed: ...` through both `_safe_print` and `background_review_callback`.
   - This specifically prevents schema errors such as `skill_manage(action='write_file')` missing `file_content` from looking like "nothing happened".

2. Bounded input snapshot.
   - The review fork receives a compact recent-history tail, controlled by `background_review.max_input_messages` and `background_review.max_input_chars`.
   - The full prior snapshot is still used for stale-tool-result de-duplication when summarizing actions.

3. Dedicated review runtime.
   - Optional top-level config:
     ```yaml
     background_review:
       provider: xiaomi
       model: mimo-v2.5-pro
       max_iterations: 8
       max_input_messages: 32
       max_input_chars: 60000
       timeout_seconds: 180
       status_path: ~/.hermes/state/background_review_status.json
      html_report_path: ~/.hermes/reports/background_review_status.html
      taskpool:
        enabled: false
        mode: suggest
    ```
   - If the configured provider differs from the parent provider, the review fork does not reuse the parent API key/base_url unless explicitly configured; provider auth should resolve normally.
   - If no background-review provider/model is configured, it inherits the parent runtime as before, including the codex_app_server → codex_responses downgrade needed for Hermes tool dispatch.

4. Wall-clock timeout.
   - `background_review.timeout_seconds` bounds the visible wait and logs/emits a timeout status. Python cannot safely kill a running thread, so the inner daemon may unwind later, but the user-visible async path is no longer silent/unbounded.

5. Status registry + HTML report.
   - Every run writes JSON status and a standalone HTML report.
   - Defaults: `~/.hermes/state/background_review_status.json` and `~/.hermes/reports/background_review_status.html`.
   - CLI: `hermes bg-review`, `hermes bg-review --json`, `hermes bg-review --html`.
   - Function API: `agent.background_review.get_background_review_status()`.
   - Status includes runtime, snapshot size, actions, failures, taskpool handoff state, and a local multi-model/conductor role plan (triager/runtime model, critic, arbiter, truth gate, evidence source).

6. Optional taskpool handoff.
   - Keep this opt-in and fail-soft: `background_review.taskpool.enabled: false` is the safe default and performs no taskpool mutation.
   - `mode: suggest` asks the review agent to emit assistant-only `BACKGROUND_REVIEW_TASKS_JSON` for complex/cross-cutting follow-up work; Hermes normalizes candidates and records them in JSON/HTML only.
   - `mode: enqueue` calls `python3 ~/.hermes/scripts/brain_task_orchestrator.py add ... --json` for each candidate and passes smart-routing metadata: `priority_layer`, `dependency_order`, `multimodel_triage_result`, `requires_multimodel`, `expected_participants`, `truth_gate`, `evidence_bundle`, capability delta, anti-drift check, and acceptance evidence.
   - Use `suggest` first in production; only enable `enqueue` after observing candidate quality and spam rate.

7. Safety invariants preserved.
   - The review fork still uses `skip_memory=True` for external providers, re-binds built-in memory/profile stores from the parent, preserves cached system prompt/session pins for prefix-cache parity, and installs memory/skills-only runtime tool whitelisting.

Verification added:
- `tests/run_agent/test_background_review_resilience.py`
- Existing bg-review suites continue to cover callback attribution, cache parity, toolset restriction, summary behavior, TUI callback, and codex-app-server integration.

## Additional recommended fixes

1. Consider adding a TUI slash command alias for `hermes bg-review` if users need in-session inspection rather than shell CLI inspection.
2. Harden skill tool prompts/schema guidance further.
   - For `skill_manage(action='write_file')`, require both `file_path` and `file_content`.
   - Prefer `skill_manage(action='patch')` for SKILL.md updates when possible.

## Reporting guidance

When reporting to the user, say whether the review:
- never triggered,
- triggered but did nothing because thresholds were not met,
- triggered and completed silently because it found no action,
- triggered and got stuck/failed.

Do not collapse these cases into "async is broken" without evidence.