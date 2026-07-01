# Advanced Patterns (from arc-dispatch production)

Extracted from `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-pipeline/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Advanced Patterns (from arc-dispatch production)

### Retry with Exponential Backoff

```python
def retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=30.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator

@retry_with_backoff(max_attempts=3, base_delay=2.0)
def run_hermes():
    return subprocess.run(cmd, timeout=600)
```

### Validator Retry Counter (prevent infinite loops)

```python
def validate_and_handle(envelope, verdict):
    if verdict["verdict"] == "reject":
        retry_count = envelope["payload"].get("retry_count", 0)
        max_retries = 2

        if retry_count >= max_retries:
            db.update_status(eid, "FAILED", error=f"rejected after {max_retries} retries")
        else:
            new_payload = {**envelope["payload"], "retry_count": retry_count + 1}
            db.set_payload(eid, new_payload)
            db.update_status(eid, "PENDING")
```

### Confirm Skip Logic (don't re-analyze)

```python
def confirm_all():
    pending = db.list_pending(type="TASK")
    need_confirm = [e for e in pending if not e["payload"].get("confirm_plan")]
    already_confirmed = [e for e in pending if e["payload"].get("confirm_plan")]
    # Only analyze tasks without confirm_plan
    for env in need_confirm:
        confirm(env)
    return already_confirmed + newly_confirmed
```

### Shared Auth Module

Extract duplicate auth code (e.g., Lark token) into single module:

```python
# lark_auth.py — shared by collector and reporter
def get_token():
    token = read_from_store()
    if expired:
        refresh()
        token = read_from_store()
    return token

# collector.py / reporter.py
import lark_auth
def _get_token():
    return lark_auth.get_token()
```

### DB Query Helpers

```python
def list_by_status(status, type=None, limit=100):
    """List envelopes by status, optionally filtered by type."""
    ...

def count_by_status():
    """Count envelopes by status. Returns {status: count} dict."""
    ...
```
