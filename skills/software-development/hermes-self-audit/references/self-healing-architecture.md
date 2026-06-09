# Self-Healing Architecture: Academic Grounding + Hermes Patterns

## Academic Frameworks (MUST reference when designing self-healing)

### MAPE-K (Kephart & Chess, 2003)
"The Vision of Autonomic Computing" — IBM's feedback loop for self-managing systems:
- **Monitor**: collect health signals (continuation backlog, handoff backlog, FD count, cron status)
- **Analyze**: compare against thresholds, detect anomalies
- **Plan**: decide corrective action (archive, delete, restart, alert)
- **Execute**: apply the fix
- **Knowledge**: shared state/config that feeds all four phases

Reference: Kephart, J.O. and Chess, D.M. (2003). "The Vision of Autonomic Computing." IEEE Computer, 36(1), 41-50.

### Erlang Supervisor Restart (Armstrong, 1993)
"One-for-one" / "one-for-all" / "rest-for-one" restart strategies:
- **one-for-one**: restart only the failed worker (e.g., restart a stuck cron job)
- **one-for-all**: restart everything when one fails (e.g., full gateway restart)
- **rest-for-one**: restart failed + downstream workers

Key principle: "let it crash" + structured recovery ≠ silent failure.

Reference: Armstrong, J. (1993). "Making Reliable Distributed Systems in the Presence of Software Errors." PhD Thesis, KTH Stockholm.

### Design by Contract (Meyer, 1992)
- **Preconditions**: what must be true before an operation
- **Postconditions**: what will be true after
- **Invariants**: what must always be true

Applied to Hermes: health checks = invariants, GC = restoring invariants, backpressure = precondition enforcement.

Reference: Meyer, B. (1992). "Applying 'Design by Contract'." IEEE Computer, 25(10), 40-51.

### Credit-Based Backpressure (Akidau et al., 2018)
Streaming Systems book: producers cannot outpace consumers. In Hermes:
- Continuation packets (producers) bounded by MAX_ACTIVE_CONTINUATIONS
- Handoff backlog bounded by dispatch tick rate
- Overflow → archive (not block, not drop)

Reference: Akidau, T., Chernyak, S. & Lax, R. (2018). "Streaming Systems." O'Reilly.

### Reactive Streams Backpressure (2015)
Specification for async stream processing with non-blocking backpressure.
Key: bounded buffer + demand signaling + overflow strategy (buffer/drop/error).

Reference: Reactive Streams Specification v1.0.0 (2015). https://www.reactive-streams.org/

### K8s Liveness/Readiness Probes
- **Liveness**: "is the process alive?" → restart if not
- **Readiness**: "can it serve traffic?" → remove from load balancer if not
- **Startup probe**: "has it finished initializing?"

Applied to Hermes: gateway FD watchdog = liveness, health score = readiness, continuation-gc = startup/cleanup.

## Self-Healing Design Template

When designing a new self-healing component, follow this structure:

```
## Component: <name>

### Academic Basis
Which framework(s) from above apply? Cite the specific work.

### Monitor (What signals?)
- Metric: <what to measure>
- Source: <where to read it>
- Frequency: <how often>

### Analyze (What thresholds?)
- GREEN: <conditions>
- YELLOW: <conditions>  
- RED: <conditions>

### Plan (What actions?)
- GREEN → no action
- YELLOW → <action> (auto-fix? alert?)
- RED → <action> (restart? escalate?)

### Execute (How?)
- Script: <path>
- Safety: <dry-run, confirmation, rollback>

### Knowledge (What persists?)
- State file: <path>
- History: <trend tracking>
```

## Hermes Health Score Components (as of 2026-05)

| Component | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| Core Services | gateway running, FD < 200 | FD 200-500 | gateway down or FD > 500 |
| Data Integrity | state.db < 500MB, WAL < 50MB | WAL 50-200MB | state.db corrupt or WAL > 200MB |
| Cron Health | 0 broken jobs | 1-5 broken | > 5 broken or no heartbeat |
| Continuation | < 200 active | 200-500 active | > 500 active |
| Handoff | < 50 pending | 50-100 pending | > 100 pending |

## Existing Self-Healing Scripts

| Script | Frequency | What it does |
|--------|-----------|--------------|
| `continuation-gc.py` | daily 04:30 | Archive >7d active, delete >30d archived |
| `unified-health-check.py` | every 4h | 5 checks → score + traffic lights + auto-gc |
| `hermes-cleanup.py` | daily 04:00 | Session TTL, snapshot cleanup, VACUUM |
| `gateway-fd-watchdog.py` | via hook | Monitor file descriptors, restart if > threshold |

## Pitfalls

1. **Don't auto-fix without logging**: Every auto-fix must produce a trace (stdout, log file, or memory) so the human can audit what happened.
2. **Don't cascade restarts**: If component A restart causes component B to fail, B should have its own restart strategy, not inherit A's.
3. **Don't alert on transient spikes**: Use sliding windows or "sustained for N checks" before alerting. A single FD spike during parallel delegation is normal.
4. **Don't mix health signals with action**: Health check = monitor only. GC/restart/cleanup = separate scripts. Keeps concerns separated and tests simpler.
5. **Academic grounding is mandatory for new patterns**: Don't invent novel self-healing approaches without checking if an established pattern exists. MAPE-K covers 90% of cases.
