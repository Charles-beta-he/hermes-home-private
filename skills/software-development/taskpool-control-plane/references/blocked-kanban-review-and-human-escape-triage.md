# Blocked Kanban Review Gates + Human-Escape Triage

Scope: Hermes local taskpool/control-plane operations where Brain task notes are the canonical task state and Kanban is an execution projection. This reference is a class-level recovery pattern for mixed blocked/review/retry queues; command names are examples for the Hermes local control plane, not global rules for unrelated task systems.

Applicability: use when the user asks to clear blocked Kanban/taskpool work and the live state contains a mix of canonical `blocked`/`review`/`retry`, Kanban `blocked` rows, and `agent_team_controller` / envelope-bus human-escape or capacity backpressure.

Anti-conditions: do not use this to bypass human review, manual approval, external side-effect permissions, multimodel certification requirements, or project-specific acceptance gates. Do not apply to non-Hermes task trackers.

## Objective

Unblock only work that is safe to re-run, advance the next dispatchable task, and preserve genuine review/proof/multimodel gates. Do not convert `review-required` or parent-ratification blockers into false progress.

## Proven sequence

1. Build a fresh two-store baseline.
   - Query canonical task notes with the orchestrator `list` and `next` commands.
   - Query the Kanban projection with stats/show/list commands.
   - Report Brain canonical and Kanban projection separately.

2. Run the canonical blocked resolver before touching Kanban projection rows.
   - Run the blocked resolver over the canonical notes.
   - It can safely move transient/unknown-gate blockers to `retry`.
   - Keep tasks blocked when the resolver says `await_auto_subtasks`, `multimodel certification still not PASS`, `explicit_requires_multimodel`, or `missing_taxonomy_artifact`.

3. Reconcile and review-close only through gates.
   - Run canonical reconcile with write enabled.
   - Run auto review close and review-gap scan.
   - Treat `PASS_ADVISORY_ONLY` as insufficient for done unless deterministic implementation/selfcheck/readback evidence exists.

4. If the envelope bus reports human escape, diagnose post-ack failures before acking.
   - Read the current escape ack watermark.
   - Query the envelope bus for `FAILED` / `BLOCKED` entries updated after the ack.
   - Classify whether failures are unrelated historical timeout/max-retry rows or current task blockers.
   - Only then acknowledge escape with a reason that names the classified failure class.
   - Verify post-ack failure/block counts are zero.

5. Dispatch at most the safe next batch.
   - Use parallel dispatch dry-run to identify selected candidates.
   - Use claim-and-handoff to claim.
   - If a claim succeeds but the command also reports another task already claimed, inspect the canonical list. A partial claim may still exist.
   - If partial claim exists and no worker was spawned, explicitly start the event-driven `consume-claimed --background` path for that claimed item.
   - Verify durable worker-job liveness and task status read-back.

6. Interpret backpressure correctly.
   - `capacity_exceeded` with an active count means a dispatchable retry is waiting behind an active boundary/worker. Do not force another worker unless the boundary policy says it is safe.
   - A healthy interim state can be: one task `running`, one retry `dispatchable=true` but skipped for capacity, and other blocked/review rows preserved by proof gates.

## Root-cause buckets to report

- `await_auto_subtasks`: parent is blocked until listed child axes finish, then parent ratification refresh must run.
- `multimodel certification still not PASS`: real non-convergence; keep blocked unless a new evidence tranche or split is generated.
- `keep_blocked_missing_taxonomy_artifact`: historical discussion artifact is unavailable; do not auto-split without replacement taxonomy/evidence. See `references/multimodel-blocked-replacement-taxonomy.md` for the safe recovery pattern.
- `explicit_requires_multimodel`: keep blocked until required model panel passes.
- `review` with `missing_ratification_or_selfcheck`: needs deterministic selfcheck/proof/readback evidence or a bounded repair task; do not auto-close.
- Advisory-only multimodel results (`PASS_ADVISORY_ONLY` + `CONTINUE_LOOP`) are not completion authority. They may justify narrowed evidence children or review handoff, but parent `done` still needs certification or deterministic implementation/readback proof.
- Kanban `review-required` rows: often represent completed worker handoffs waiting for human/proof review, not service blockage.

## Pitfalls

- Do not bulk-unblock projection rows whose latest summary says `review-required`; Kanban blocked can be the correct projection of a review gate.
- Do not treat Kanban `blocked` count as proof the service is blocked. Compare with canonical `next`, active workers, and envelope state.
- Do not acknowledge human escape just to resume work; first prove post-ack failures are understood and not current unsafe blockers.
- Do not claim that `next=null` means no work if a task is currently `running`; it can mean all additional candidates are blocked or capacity-limited.
- Do not demote or force-close tasks already in `review` because a late worker/envelope timed out; use review gap scan and proof gates.
- If a PID-based worker/job liveness check reports an old job alive, verify command identity as well as PID existence; on macOS, PIDs can be reused by unrelated processes, which creates false-running/false-alive projections if only `os.kill(pid, 0)` is used.
