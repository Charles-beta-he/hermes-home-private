# Replay-Based Regression Testing (Traffic-Driven)

Extracted from `/Users/charles/.hermes/skills/software-development/test-driven-development/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Replay-Based Regression Testing (Traffic-Driven)

When a system has routing/dispatch logic (URL routers, intent classifiers, command matchers, LLM query classifiers), **hardcoded test cases drift from reality**. The user's inputs are unpredictable and diverse — you can't anticipate every phrasing.

**Pattern: Record → Replay → Detect Drift**

1. **Record**: On every live request, persist `(input, route_id, payload_snapshot)` to a local review store. This is cheap — just a JSON write.
2. **Replay**: Periodically (batch trigger, e.g. every N records), re-run the routing logic against each recorded input and compare the new `route_id` against the recorded one.
3. **Drift**: If they differ, you've caught a regression before the user does. Generate a regression test case from the drifted record.

**Critical rule: Import real handlers, never duplicate matching logic.**
The replay verifier must call the same handler functions that production uses. If you copy pattern-matching into the test, it will silently drift when production code changes — defeating the entire purpose.

```python
# CORRECT: import and call real handlers
import app
def replay(ctx):
    return app.handle_l0_query(ctx.user_text)

# WRONG: copy matching logic into test
def replay(ctx):
    if "天气" in ctx.user_text:  # Duplicates app.py!
        return "weather", "..."
```

**Circular import avoidance**: If the replay tool can't import the app module directly (e.g. FastAPI app module imports the recording module), use subprocess:
```python
proc = await asyncio.create_subprocess_exec(
    python_bin, "replay_verify.py", "--json",
    stdout=asyncio.subprocess.PIPE,
)
```

**Hot-path safety**: Never replay synchronously in the request path. Use batch triggers (count threshold since last replay) and run as a background task.

**Stub payloads for offline replay**: When replaying without a real server, create lightweight stub objects that provide attribute access matching the production model:
```python
class _MessageStub:
    """Wraps a dict to provide .role / .type / .image_url attribute access."""
    def __init__(self, data):
        self._data = data
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._data.get(name)
```

**Expected drift vs unexpected drift**: When you fix a routing bug, old records will show `recorded_route_id=wrong, replayed_route_id=correct`. This is expected — not a regression. Only flag cases where the new route is unexpected.

For a complete implementation example, see `references/replay-based-regression-testing.md`.
