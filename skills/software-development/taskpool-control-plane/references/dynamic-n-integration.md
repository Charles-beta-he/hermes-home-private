# Dynamic N Integration into brain_task_orchestrator

## Problem

`brain_task_orchestrator.py` had hardcoded `max_agents=3` in multiple call sites, ignoring the dynamic N module (`~/.hermes/scripts/dynamic_n.py`) that computes parallel agent count from actual taskpool state.

## Solution

Replace all hardcoded `max_agents` defaults with `get_smoothed_n(dispatchable_count, group_count)` calls.

### Formula

```
raw_n = min(ceil(dispatchable / 7), conflict_groups, 3)
applied_n = smoothed(raw_n, SMOOTHING_CYCLES=2)
```

- `dispatchable`: count of tasks passing `is_dispatchable()` (status=pending, no blockers, no active claims)
- `conflict_groups`: count of unique `conflict_group` or `parallel_boundary` values among candidates
- Cap: 3 (hard max)
- Smoothing: candidate must sustain for 2 consecutive cycles before `applied_n` changes

### Integration Pattern

Each call site that previously used `max_agents=3` must independently:

1. Compute `dispatchable_count` and `group_count` from current state
2. Call `get_smoothed_n(dispatchable_count, group_count)` 
3. Extract `applied_n` from result
4. Pass `applied_n` as `max_agents`

Do NOT use a shared `_resolve_max_agents()` helper with stale counts — each call site must compute its own context.

### Call Sites Fixed (2026-05-28)

1. **`command_dispatch_dry_run()`** — dispatch dry-run
2. **`command_parallel_claim_and_handoff()`** — parallel claim
3. **`command_evidence_spine()`** — evidence spine generation
4. **`dispatch_one_task_json()`** — single task dispatch

All use the same pattern:
```python
# Import at top
try:
    from dynamic_n import get_smoothed_n
except ImportError:
    get_smoothed_n = None

# At call site
candidates = dispatchable_tasks()  # or equivalent
groups = set()
for t in candidates:
    g = str(t.fm.get("conflict_group") or t.fm.get("parallel_boundary") or "").strip()
    if g:
        groups.add(g)
if get_smoothed_n is not None:
    n_result = get_smoothed_n(len(candidates), max(len(groups), 1))
    max_agents = max(1, int(n_result.get("applied_n", 3)))
else:
    max_agents = 3  # fallback
```

### Pitfalls

1. **State pollution**: `get_smoothed_n()` modifies `~/.hermes/dynamic_n_state.json` as a side effect. Calling it with test/debug data corrupts the smoothing history. Always reset state after testing:
   ```python
   from dynamic_n import save_state, STATE_FILE
   save_state({'current_n': expected_n, 'candidate_n': None, 'candidate_count': 0, 'history': []})
   ```

2. **Smoothing delay**: When task count changes significantly, `applied_n` won't reflect the new raw_n until 2 consecutive cycles produce the same value. This is intentional — prevents flapping.

3. **conflict_groups=0**: Always pass `max(len(groups), 1)` to avoid division issues. A single group means no boundary conflicts (everything can run together).

4. **Import fallback**: `dynamic_n.py` may not be importable in all contexts. Always guard with `try/except ImportError` and fall back to hardcoded 3.

5. **Explicit override**: CLI `--max-agents N` must always override dynamic N when N >= 1. The dynamic path only activates when no explicit value is given.

### Verification

```bash
# Check current dynamic N state
python3 ~/.hermes/scripts/dynamic_n.py state

# Verify dispatch uses dynamic N (should show non-3 max_agents when groups < 3)
python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json | python3 -c "
import json, sys
data = json.loads(sys.stdin.read(), strict=False)
print(f'max_agents: {data.get(\"max_agents\", \"not in output\")}')
"

# Verify parallel claim uses dynamic N
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-claim-and-handoff --json | python3 -c "
import json, sys
data = json.loads(sys.stdin.read(), strict=False)
print(f'max_agents: {data.get(\"max_agents\", \"not in output\")}')
"
```
