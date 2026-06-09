# Continuation Control Plane

Use this reference when generalizing Hermes auto-relay / budget handoff behavior across conversation, delegation, taskpool, bg-review, cron, and gateway delivery.

## Principle

All potentially unfinished work should move from call-stack state to durable packet state:

Detect -> Packet -> Resume -> Verify -> Close

Do not copy recursive auto-relay logic into every subsystem. Use a shared continuation packet schema and subsystem-specific runners.

## Landed minimum viable control plane

Core module:

- `agent/continuation.py`

Provides:

- `ContinuationPacket`
- `build_continuation_packet(...)`
- `write_continuation_packet(...)`
- `write_legacy_relay_packet(...)`
- `continuation_status(...)`
- `normalize_continuation_reason(...)`

Default registry:

- `~/.hermes/state/continuations/active/`
- `~/.hermes/state/continuations/completed/`
- `~/.hermes/state/continuations/failed/`
- `~/.hermes/state/continuations/archived/`

Conversation auto-relay compatibility path remains:

- `~/.hermes/state/relay-packets/`

But contents now use `hermes_continuation_packet_v1` and store legacy information under `metadata.legacy_schema`.

## Packet schema

Canonical schema: `hermes_continuation_packet_v1`.

Important fields:

- `packet_id`
- `scope`: `conversation`, `delegate`, `taskpool`, `cron`, `bg_review`, `gateway`, etc.
- `reason`: normalized reason such as `max_iterations`, `budget_exhausted`, `provider_timeout`
- `raw_reason`: exact original exit reason
- `summary`
- `remaining_work`
- `evidence`
- `resume`: policy/executor metadata
- `delivery`: delivery metadata for gateway/cron use
- `limits`: bounded retry/relay counters
- `metadata`: compatibility or subsystem-specific details

## Current integrations

1. `agent/conversation_loop.py`
   - Auto-relay writes a global continuation packet plus a relay-compatible packet.
   - Treats both `budget_exhausted` and `max_iterations_reached(...)` as relay-eligible.
   - Keeps recursion bounded by `delegation.max_relay_count`.

2. `~/.hermes/scripts/brain_task_dispatch_tick.py`
   - Adds `continuation` to tick summaries.
   - Reports `active_count`, `counts`, `by_scope`, and `backlog_warning`.

3. Config:

```yaml
taskpool:
  continuation_backlog_threshold: 100
```

## Verification

Run focused tests:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python -m pytest \
  tests/agent/test_continuation.py \
  tests/run_agent/test_auto_relay_continuation.py \
  tests/run_agent/test_taskpool_dispatch_tick_runtime.py \
  tests/scripts/test_continuation_fragmentation_guard.py \
  -q -o addopts=
python3 -m py_compile agent/continuation.py agent/conversation_loop.py agent/agent_init.py ~/.hermes/scripts/brain_task_dispatch_tick.py
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --no-state --no-blocked-resolve-step
```

## Anti-fragmentation governance

To prevent future Hermes evolution from inventing parallel handoff/relay systems, every new or modified unfinished-work path must pass this gate before implementation:

1. Interface first: use `agent.continuation` unless the change proves the canonical schema cannot represent the case.
2. ADR requirement: if a subsystem wants a new handoff file, queue, retry ledger, or resume state, document why `hermes_continuation_packet_v1` is insufficient before adding it.
3. Registry visibility: resumable work must appear in `continuation_status(...)` or in a summary that references a continuation packet id.
4. Ownership: every packet-producing subsystem must declare exactly one owner/runner and a claim/idempotency rule.
5. Closure gate: every runner must define evidence required to move a packet out of `active/`.
6. Tests as ratchet: each new scope needs at least one packet schema test and one observability/status test.
7. Post-update guard: implemented as `continuation_fragmentation_guard` in `~/.hermes/scripts/post-update-check.py`. It scans Hermes repo code plus user scripts for ad-hoc `.hermes/state/*handoff*|*relay*|*resume*|*retry*|*recovery*|*missed*` writers that do not use `agent.continuation`.

Code-review smell: any new directory under `~/.hermes/state/` named `*handoff*`, `*relay*`, `*resume*`, or `*retry*` should be challenged unless it stores/references a canonical continuation packet. The self-check should stay conservative: flag durable resumable-state writers, not ordinary in-memory retry loops or read-only mentions.

## Next expansion order

1. `delegate_task`: child budget exhaustion should return a child continuation packet instead of only a summary.
2. taskpool handoffs: autorun/parallel handoff files should reference continuation packet IDs.
3. bg-review: timeouts should write `scope=bg_review` packets for next idle/tick recovery.
4. cron: missed/timeout runs should write `scope=cron` packets with bounded next-tick retry.
5. gateway: delivery failures should write `scope=gateway` packets with target/thread metadata.

## Goal-bound relay refresh and clean-session handoff

When `max_relay_count` is exhausted, keep the default safe: at most one explicit auto refresh. A bounded multi-refresh policy is allowed only in explicit goal-bound mode with machine-verifiable closure boundaries such as `lark_task_ids`, `taskpool_task_ids`, `checklist_ids`, `acceptance_commands`, or `requirement_ids`. Reject open-ended boundaries (`until_satisfied`, natural-language-only goals), missing evidence, missing remaining work, exhausted task/global caps, stale external task state, or duplicate side-effect risk.

For context/compression exhaustion, use packet-backed clean-session handoff rather than summary-only continuation. `agent.continuation` now carries structured fields for `completed_work`, `goal_boundary`, `side_effect_ledger`, `refusal_flags`, and `freshness_requirements`, plus helpers `evaluate_continuation_eligibility(...)` and `build_clean_session_handoff(...)`. The prior natural-language summary is non-authoritative metadata; the durable continuation packet and evidence bundle are the authority.

Verification slice:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python -m pytest tests/agent/test_continuation.py tests/run_agent/test_auto_relay_continuation.py -q -o addopts=
python3 -m py_compile agent/continuation.py agent/conversation_loop.py agent/agent_init.py
python3 ~/.hermes/scripts/post-update-check.py --fix
```

## Pitfalls

- Do not create unbounded recursive relay; every scope needs retry/relay limits.
- Do not let multiple owners resume the same packet without a claim/idempotency key.
- A packet is not proof of completion; closure requires scope-specific verification.
- Never treat the last natural-language summary as proof. It may seed comprehension, but continuation authority must come from structured packet fields and evidence pointers.
- Goal-bound auto mode must remain explicit opt-in with both task-level and global hard caps.
- `max_iterations_reached(...)` remains a real-world budget-exhaustion reason and must not be dropped.
