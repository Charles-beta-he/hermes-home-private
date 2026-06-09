# Brain Taskpool Retry Task Diagnosis

When the user asks "what tasks are in retry" or "任务池retry的都是什么任务", use this pattern to query and classify retry tasks.

## Query Pattern

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
retry_tasks = [t for t in data.get('rows', []) if t.get('status') == 'retry']
print(f'总数: {data[\"task_count\"]}')
print(f'retry状态: {len(retry_tasks)}')
for t in retry_tasks:
    print(f'--- {t[\"id\"][:80]}')
    print(f'  标题: {t[\"title\"][:120]}')
    print(f'  retry_count: {t[\"retry_count\"]}')
    print(f'  next_attempt_at: {t.get(\"next_attempt_at\", \"N/A\")}')
    print(f'  project: {t[\"project\"]}')
    print(f'  priority: {t[\"priority\"]}')
    print(f'  brain: {t[\"brain\"]}')
    print(f'  lane: {t[\"lane\"]}')
    # Extract retry reason from proof log
    body = t.get('body', '')
    retry_lines = [l.strip() for l in body.split('\n') if 'retry' in l.lower()]
    if retry_lines:
        print(f'  最后retry原因: {retry_lines[-1][:200]}')
"
```

## Retry Failure Patterns

Two distinct failure modes drive tasks into `retry` status:

### 1. Worker Timed Out Without Proof

```
Lifecycle transition `running` -> `retry` by `hermes-parallel`.
Reason: event-driven worker timed out without proof; requeue for proof-gated retry
Evidence: command:agent_team_controller consume-claimed worker timeout
```

**Cause:** The parallel worker ran but did not produce a PROOF_JSON artifact before the timeout (typically 600s for code tasks, 300s for analysis).

**Diagnosis:**
- Check `retry_count` — count >= 2 suggests the task may be too complex for a single worker run
- Check task scope — large Lark tasks with multiple acceptance criteria may need decomposition
- Check if the task's `parallel_boundary` conflicts with other running tasks

**Fix options:**
- Let retry proceed (next_attempt_at will trigger automatic re-dispatch)
- Decompose the task into smaller subtasks if retry_count >= 2
- Increase worker timeout if the task is legitimately long-running

### 2. Stale Running Retry

```
Reconcile action `stale_running_retry` by `next`. Previous status `running`.
```

**Cause:** The task was `running` but the reconcile sweep found it stale (no heartbeat, no proof, claim expired). The reconcile automatically moves it to `retry`.

**Diagnosis:**
- Check if the worker process died silently (OOM, crash, human escape)
- Check `agent_team_controller.py status` for human_escape_triggered state
- Look for envelope_bus entries: `from envelope_bus import list_by_status; list_by_status('FAILED')`

**Fix options:**
- Retry will proceed automatically on next dispatch tick
- If persistent, check envelope bus for crash patterns
- If human_escape triggered, ack the escape before retrying

## Status Lifecycle for Retry

```
pending -> claimed -> running -> retry -> (reconcile promotes) -> pending -> claimed -> ...
```

Key fields on retry tasks:
- `retry_count`: number of retry attempts (escalation threshold typically at 2-3)
- `next_attempt_at`: ISO timestamp when reconcile will promote back to `pending`
- `stale_claim`: whether the claim is still held (should be false after retry transition)

## Distinguishing from Blocked Tasks

Retry ≠ Blocked:
- **retry**: transient failure, will auto-retry after delay
- **blocked**: needs external input (human decision, multimodel certification, evidence fix)

Check `lifecycle_next` field:
- retry tasks: `["pending", "claimed", "blocked", "archived", "expired"]`
- blocked tasks: typically need `blocked-resolve-step` or human intervention

## Aggregated Status Dashboard

For a full status distribution:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json 2>/dev/null | python3 -c "
import json, sys
from collections import Counter
data = json.load(sys.stdin)
counts = Counter(t.get('status') for t in data.get('rows', []))
print(f'总数: {data[\"task_count\"]}')
for status, count in counts.most_common():
    print(f'  {status}: {count}')
"
```

## Related

- `references/agent-team-parallel.md` — parallel worker architecture, timeout values, envelope bus
- `references/cycle-timeout-diagnostics.md` — diagnosing hung worker cycles
- `references/stale-claim-and-finished-subtasks.md` — stale claim recovery pattern
