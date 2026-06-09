# Escape-Triggered Cron Alert Pattern

Session: 2026-06-01 pipeline_tick escape detection and triage

## The Precedence Problem

Cron tick output has two competing rules:
1. **Silent rule**: `If new_envelopes=0 and timeouts_handled=0, output nothing (silent).`
2. **Escape rule**: `If escape_triggered=true, ALERT prominently.`

When both fire simultaneously (nothing new happened BUT escape is active), **escape takes precedence**. The escape state is a safety-critical signal — the pipeline is paused and no work is dispatching. Silencing it because "nothing new happened" would hide the fact that the pipeline is broken.

### Correct cron behavior:
```
tick → new_envelopes=0, timeouts=0, escape_triggered=true
→ ALERT (not silent)
```

The `pipeline_tick.py tick` command returns both signals. The cron agent must check `escape_triggered` AFTER processing the new_envelopes/timeouts counts. If escape is active, always produce a prominent alert regardless of the other counts.

## Failure Migration Pattern

After ACKing one failure class, a *different* failure class can re-trigger escape within hours. This is not a regression — it's the pipeline cleaning up enough to surface the next bottleneck.

### Observed sequence:
1. **Phase 1**: HTTP 429 rate-limit failures dominate (infrastructure issue)
2. Human ACKs: "Reviewed provider-429 false-running root cause; patched..."
3. **Phase 2**: Proof-gate failures (`missing_proof`, `invalid_proof`) and stale-running cleanup emerge
4. Escape re-triggers within 8.5 hours

### Why this happens:
- Phase 1 failures (429) were masking Phase 2 failures — workers that would have failed on proof gates were instead failing on API errors first
- After fixing 429, workers now actually reach the proof validation step
- The proof-gate failures were always there, just hidden behind the infrastructure failures

### Triage decision tree:
```
escape_triggered=true
  → classify post-ack failures by type
  → if all same type: systematic worker issue, fix before ACKing
  → if mixed types: check if new types are "previously masked" failures
    → if yes: they represent real worker quality issues, not regressions
    → fix the most common one, ACK, expect the next class to surface
```

## Diagnostic Workflow for Cron Agent

When `pipeline_tick.py tick` returns `escape_triggered=true`:

```bash
# 1. Get bus stats (already in tick output, but verify)
python3 ~/.hermes/scripts/envelope_bus.py stats

# 2. Query post-ack FAILED envelopes
python3 -c "
import sqlite3, json, os
conn = sqlite3.connect(os.path.expanduser('~/.hermes/state/envelope_bus.db'))
conn.row_factory = sqlite3.Row
ack = json.load(open(os.path.expanduser('~/.hermes/state/envelope_escape_ack.json')))
acked_at = ack.get('acked_at', '1970-01-01T00:00:00Z')
rows = conn.execute(
    'SELECT id, title, error, updated_at FROM envelopes WHERE status=\"FAILED\" AND updated_at > ? ORDER BY updated_at DESC',
    (acked_at,)
).fetchall()
for r in rows:
    print(f'[{r[\"id\"]}] {r[\"title\"][:80]}  error={str(r[\"error\"])[:120]}  at={r[\"updated_at\"]}')
"

# 3. Classify failures
# - missing_proof / invalid_proof → proof gate (worker prompt issue)
# - HTTP 429 / 500 → infrastructure (transient, ACK-worthy)
# - stale RUNNING → timeout/appetite (task sizing issue)
# - missing + stale in same window → mixed (see migration pattern above)

# 4. Produce alert with:
#    - Failure count since last ack
#    - Classified failure types
#    - Recommendation: ACK, fix, or escalate
```

## Report Format (for cron output)

```
## ⚠️ HUMAN ESCAPE TRIGGERED — Dispatch Paused

**Tick**: <timestamp>
- New envelopes: N
- Timeouts handled: N
- Escape triggered: YES

### Escape Threshold Breached
Since last ack (<acked_at>): X blocks, Y failures — hits ≥Z threshold.

**Failure classification since last ack:**
| Envelope | Task | Error | When |
|---|---|---|---|
| ... | ... | ... | ... |

### Assessment
<brief analysis: same failure class as before? new class? migration pattern?>

### Recommendation
<ACK + retry / fix worker prompt / split task / escalate to human>
```
