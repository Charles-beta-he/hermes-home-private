---
name: hermes-self-improvement-pipeline
category: software-development
description: "Use when operate and debug the self-improvement pipeline (~/.hermes/scripts/self-improvement-pipeline.py). Covers ROI calculation, signal sourcing, stuck detection, and pipeline unblocking. Use when pipeline shows 'no actionable items' for 3+ days, ROI capping issues, or missing signal sources."
triggers:
  - "self-improvement pipeline"
  - "no actionable improvement items"
  - "pipeline stuck"
  - "ROI cap"
  - "fix_tool_config"
  - "improvement pipeline"
  - "self-improvement stuck"
  - "pipeline unblock"
  - "evolve.log"
  - "improvement-action-plan"
---

# Self-Improvement Pipeline Operations

## Overview

Operate and debug the self-improvement pipeline (~/.hermes/scripts/self-improvement-pipeline.py). Covers ROI calculation, signal sourcing, stuck detection, and pipeline unblocking. Use when pipeline shows 'no actionable items' for 3+ days, ROI capping issues, or missing signal sources. This skill is maintained as a `monitor`-shaped contract: it should guide watching, alerting, dashboards, health checks, or scheduled observation without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `hermes-self-improvement-pipeline` and requires watching, alerting, dashboards, health checks, or scheduled observation.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Operates `~/.hermes/scripts/self-improvement-pipeline.py` — the system that detects and prioritizes Hermes improvements from autopsy, health, evolution momentum, and operational signals.

## Architecture

```
Signal Sources → Pipeline → ROI Scoring → Action Plan → (auto-exec)
     ↑               ↓
  autopsy         fix_tool_config / fix_cron_health /
  health          execute_stalled_proposals / etc.
  proposals
  operational_health
```

### Key Files

- Script: `~/.hermes/scripts/self-improvement-pipeline.py`
- Evolve log: `~/.hermes/logs/evolve.log`
- Action plan: `~/.hermes/notes/improvement-action-plan.json`
- Stuck counter: `~/.hermes/notes/pipeline-stuck-counter.json`
- Autopsy: `~/.hermes/memory/autopsies/*.json` (limit 50)
- Health: `~/.hermes/notes/health-log.jsonl` (limit 200)
- Proposals: `~/.hermes/notes/proposals.jsonl`
- Usage score: `~/.hermes/notes/usage-score.json`

## Common Failure: "no actionable improvement items"

This happens when ALL signals are blocked by:
1. `fix_tool_config` ROI cap (`_FIX_TOOL_CONFIG_MAX_ROI=1.75`) prevents re-processing
2. `EVOLUTION_COOLDOWN_DAYS=7` blocks too-recent evolution signals
3. `MIN_CONFIDENCE=0.65` filters out low-confidence proposals
4. Missing signal sources (operational_health, proposal_expiry not implemented)

### Debugging Steps

```bash
# 1. Check how many days stuck
python3 ~/.hermes/scripts/self-improvement-pipeline.py --json 2>/dev/null | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'Total: {d[\"summary\"][\"total\"]}')
print(f'fix_tool_config ROI cap: {d.get(\"meta\",{}).get(\"_FIX_TOOL_CONFIG_MAX_ROI\",\"N/A\")}')
"

# 2. Check stuck counter
cat ~/.hermes/notes/pipeline-stuck-counter.json 2>/dev/null

# 3. Check evolve.log for recent entries
tail -5 ~/.hermes/logs/evolve.log | python3 -c "
import sys,json
for line in sys.stdin:
    d=json.loads(line)
    print(f'{d[\"ts\"][:10]} eval={d[\"eval_result\"]} useful={d[\"useful_evolution\"]}')
"

# 4. Check usage-score for cron health
python3 -c "
import json
with open('/Users/charles/.hermes/notes/usage-score.json') as f: d=json.load(f)
print(f'cron_green: {d.get(\"cron_green\",{})}')
"

# 5. Check proposal backlog
wc -l ~/.hermes/notes/proposals.jsonl 2>/dev/null
```

### Fix Patterns

#### Pattern A: Cumulative ROI (fix_tool_config blocked)

The `fix_tool_config` action type has a ROI cap of 1.75×. When the same tool config keeps failing, the cap prevents re-escalation. Fix: apply cumulative ROI with a cap (e.g., 20×).

```python
# In _score_action(), replace single ROI with cumulative:
CUMULATIVE_OCCURRENCE_CAP = 20
def _cumulative_roi(base_roi: float, occurrence_count: int) -> float:
    capped = min(occurrence_count, CUMULATIVE_OCCURRENCE_CAP)
    return round(base_roi * (1 + 0.5 * (capped - 1)), 2)
```

#### Pattern B: Missing signal sources

Pipeline only reads autopsy/health/proposals. Add operational_health and proposal_expiry:

```python
# operational_health: cron health → signals
ops = _load_operational_health_signals()
# Reads usage-score.json cron_green.bad count

# proposal_expiry: stuck proposals → signals
expired = _load_proposal_expiry_signals()
# Reads proposals.jsonl, items with status='proposed' and age > PROPOSAL_EXPIRY_DAYS
```

#### Pattern C: Stuck-counter mechanism

When pipeline skips all actions for 5+ consecutive runs, auto-lower the threshold:

```python
STUCK_COUNTER_PATH = os.path.join(NOTES_DIR, "pipeline-stuck-counter.json")
STUCK_THRESHOLD = 5
UNSTUCK_ROI_DELTA = 0.3

def _get_effective_min_roi() -> float:
    counter = _load_stuck_counter()
    skip_count = counter.get("skip_count", 0)
    if skip_count >= STUCK_THRESHOLD:
        return max(MIN_ROI - UNSTUCK_ROI_DELTA, 0.1)
    return MIN_ROI
```

## Action Types

| Action Type | ROI Source | Threshold | Description |
|---|---|---|---|
| `fix_tool_config` | Autopsy (tool usage) | 1.75× cap | Tool config missing/broken |
| `fix_cron_health` | Operational health | 3.5× | Cron jobs in bad state |
| `execute_stalled_proposals` | Proposal expiry | 1.8× | Proposals stuck >7 days |
| `general_improvement` | Health records | varies | Generic improvement |

## Running

```bash
# Dry run (read-only)
python3 ~/.hermes/scripts/self-improvement-pipeline.py

# Auto-execute
python3 ~/.hermes/scripts/self-improvement-pipeline.py --auto-exec

# JSON output
python3 ~/.hermes/scripts/self-improvement-pipeline.py --json
```

## Phase 1: Behavioral Benchmarks (Goodhart Fix)

Old benchmarks checked file *existence* (e.g. "does proposals.jsonl exist?") — classic Goodhart's Law. New benchmarks test *runtime behavior*:

```bash
python3 ~/.hermes/scripts/behavioral-benchmark-runner.py
```

**10 benchmarks:**
1. Pipeline produces actionable items (not empty)
2. Post-update check passes all guards
3. Hook registry selfcheck passes
4. Usage score computed, grade A or B
5. PUA-loop dashboard has recent data (<48h)
6. Memory files under char limit
7. State DB integrity (PRAGMA integrity_check)
8. Skills count > 200
9. Cron bad count < 5
10. Pipeline produced items in last 24h

Results: `~/.hermes/pua-loop/benchmark_runs.jsonl` (JSONL, append-only)

Cron: daily at 02:30 (`behavioral-benchmark-daily`, no_agent=true)

## Phase 2: Benchmark Regression Signals

Pipeline now reads `benchmark_runs.jsonl` and generates signals when:
- Pass rate regresses (e.g. 100% → 90%)
- New failures appear (items that passed last run now fail)

Signal types: `benchmark_regression` (impact=7), `benchmark_new_failure` (impact=6)
Action type: `fix_benchmark_regression` → run benchmark runner, fix failing tests

## Pitfalls

- `fix_tool_config` ROI cap (1.75×) is intentional — prevents infinite retry of same broken config
- `EVOLUTION_COOLDOWN_DAYS=7` prevents re-processing recent improvements
- `MIN_CONFIDENCE=0.65` filters low-quality proposals — don't lower without evidence
- Stuck-counter auto-lowers threshold, not bypasses it — still respects MIN_ROI
- operational_health reads `usage-score.json` cron_green.bad — ensure cron-health-quarantine.py runs regularly
- proposal_expiry reads `proposals.jsonl` — proposals must have `status='proposed'` and `created_at` field
- Action plan saved to `~/.hermes/notes/improvement-action-plan.json` — overwritten each run
- **subprocess stdout truncation**: NEVER slice `r.stdout[-2000:]` in `run_script()` helpers — this breaks JSON parsing by cutting the opening brace. Use full stdout, only truncate stderr. This bug caused 100% benchmark failure rate until fixed.
- **Cron schedule 429s**: Multiple jobs at identical times (e.g. all at `3 2 * * *`) cause Gemini 429 rate limits. Stagger: `3 2`, `5 2`, `8 2`, `10 2`, `13 2`, `15 2`. Read `jobs.json` directly (not `crontab -l`) to see all jobs.
- Behavioral benchmark runner: `validate_json_output()` needs FULL stdout — truncated JSON always fails validation

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
