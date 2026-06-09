# Replay-Based Regression Testing — Implementation Reference

## Motivation

Hardcoded regression tests for routing/dispatch systems drift from reality because:
- User inputs are unpredictable — you can't anticipate every phrasing
- Manual screenshot-to-test pipelines only cover what someone happened to see
- Pattern-matching code duplicated in tests silently diverges from production

The correct approach: **record live traffic, replay against real handlers, detect drift**.

## Architecture

```
Live Request → Handler → Response → schedule_review(payload, user_text, route_id)
                                           ↓
                                    write JSON record to local store
                                           ↓
                                    batch trigger (every N records)
                                           ↓
                                    replay_verify.py reads records
                                           ↓
                                    for each record:
                                      import app → call real handler(user_text)
                                      compare replayed route_id vs recorded
                                           ↓
                                    drift detected → generate regression test
```

## Key Files (Rokid Bridge Example)

| File | Role |
|------|------|
| `rokid_dev_review.py` | Records `(user_text, route_id, payload)` after each SSE dialogue |
| `replay_verifier.py` | Core engine: `load_review_records()`, `replay_record()`, `replay_records()` |
| `replay_verify.py` | CLI entry: imports real handlers from `app.py`, runs batch replay |
| `tests/test_replay_verifier.py` | Tests for the verifier itself |

## Stub Payload Pattern

When replaying offline (no real HTTP request), create lightweight stubs that provide attribute access matching the production Pydantic model:

```python
class _MessageStub:
    """Wraps a message dict to provide .role / .type / .image_url attribute access."""
    def __init__(self, data: dict):
        self._data = data
    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._data.get(name)

class _StubPayload:
    """Stand-in for production Pydantic model during offline replay."""
    def __init__(self, data: dict):
        raw_messages = data.get("message") or data.get("messages") or []
        self._messages = [_MessageStub(m) if isinstance(m, dict) else m for m in raw_messages]
        self._data = {**data, "message": self._messages}

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name == "message":
            return self._messages
        return self._data.get(name)
```

This lets functions like `extract_image_urls(payload)` work correctly during replay without importing the full Pydantic model stack.

## Circular Import Avoidance

If `app.py` imports the recording module (`rokid_dev_review.py`), the replay tool cannot `import app` directly. Solution: run the replay as a subprocess.

```python
async def _run_replay_verification():
    proc = await asyncio.create_subprocess_exec(
        python_bin, "replay_verify.py", "--limit", "200", "--json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    # Save summary JSON
    summary_path.write_text(stdout.decode(), encoding="utf-8")
```

## Batch Trigger Design

Never replay on every request. Use a count-based trigger:

```python
_REPLAY_THRESHOLD = int(os.getenv("ROKID_REPLAY_VERIFY_THRESHOLD", "10"))

def _maybe_trigger_replay():
    count = _records_since_last_replay()
    if count < _REPLAY_THRESHOLD:
        return
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_run_replay_verification())
    except RuntimeError:
        pass
```

Call `_maybe_trigger_replay()` at the end of the recording function (after the record is written).

## CLI Interface

```bash
# Verify last 50 records (default)
python3 replay_verify.py

# Verify last 200, JSON output
python3 replay_verify.py --limit 200 --json

# Only records since a timestamp
python3 replay_verify.py --since 1700000000

# Generate regression test file for drifted records
python3 replay_verify.py --generate tests/test_replay_drift.py
```

## Expected vs Unexpected Drift

When a routing bug is fixed, old records show:
- `recorded_route_id = "model_fallback"` (the wrong route)
- `replayed_route_id = "text_l0"` (the correct route after fix)

This is **expected drift** — the code improved. Only unexpected drift (new route worse than old) indicates a regression.

## Output Format

```json
{
  "total": 50,
  "matched": 48,
  "drifted": 2,
  "drift_rate": 0.04,
  "mismatches": [
    {
      "user_text": "...",
      "recorded_route_id": "image_placeholder",
      "replayed_route_id": "model_fallback",
      "record_path": "/path/to/record.json"
    }
  ]
}
```

## Pitfalls

1. **Duplicating matching logic in replay tool** — must import real handlers.
2. **Blocking the hot path** — always batch-trigger + background.
3. **Stub payload missing attribute access** — dict-based payloads need `_MessageStub` wrapping for functions that access `.role`, `.type`, etc.
4. **Treating all drift as regression** — distinguish expected (bug fix) from unexpected (new bug).
5. **Not counting records since last replay efficiently** — use `created_at` timestamp comparison, not full scan.
