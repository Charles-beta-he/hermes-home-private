# Force-Promoting Retry Tasks After Infrastructure Fix

When retry tasks are waiting for their `next_attempt_at` and the infrastructure issue that caused the failure has been fixed, skip the delay instead of waiting.

## Pattern

```bash
# 1. Identify retry tasks
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json 2>/dev/null | python3 -c "
import json, sys
data = json.loads(sys.stdin.read(), strict=False)
retry = [t for t in data['rows'] if t['status'] == 'retry']
for t in retry:
    print(f'{t[\"id\"]}  rc={t[\"retry_count\"]}  next={t.get(\"next_attempt_at\",\"\")}')
"

# 2. Force-promote each to pending (override next_attempt_at)
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "<task-id>" \
  --to pending --actor hermes \
  --reason "infra-fixed: <what was fixed>" \
  --force --json

# 3. Dispatch
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-claim-and-handoff --write --json
```

## When to use

After fixing infrastructure that caused cascade worker failures:
- MCP server connection failures (path fix, config fix, restart)
- Model fallback chain deployed (provider outage mitigation)
- Workspace sync barrier added (parallel worktree conflicts)
- SDK circuit breaker installed (null response crashes)
- Network/proxy fixes

## Verification

After promotion + dispatch:
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json 2>/dev/null | python3 -c "
import json, sys
from collections import Counter
data = json.loads(sys.stdin.read(), strict=False)
counts = Counter(t['status'] for t in data['rows'])
for s, c in counts.most_common():
    print(f'  {s}: {c}')
claimed = [t for t in data['rows'] if t['status'] == 'claimed']
for t in claimed:
    print(f'  CLAIMED: {t[\"id\"][:60]}')
"
```

Expected: promoted tasks appear as `claimed` (dispatched) or `pending` (queued for next dispatch cycle). None should remain in `retry`.

## Pitfalls

- `transition --to pending` without `--force` will fail if `next_attempt_at` hasn't passed yet. Always use `--force` for immediate promotion.
- The `--reason` field is recorded in the task's proof log. Document what infrastructure fix enables the retry.
- Don't promote retry tasks before the underlying issue is fixed — they'll just fail again and increment `retry_count`.
- If `parallel-claim-and-handoff --write` returns `claimed: false`, check `dispatch-dry-run` to see if there's a dispatchability blocker beyond the retry status.
