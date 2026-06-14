# Terminal Ladder vs Whole-Program Completion Review

Use when a governed workflow sequence reports a terminal state (for example an empty next-ladder) and the user asks whether the broader long-term plan is complete.

## Core lesson

A terminal ladder proves only that the current sequence has no safe automatic next phase. It does not prove the whole program, mission, or long-term stable plan is finished. Completion requires comparing the terminal ladder against the canonical target model and live control-plane health.

## Procedure

1. **Find the canonical target model**
   - Read the long-term plan, implementation packet, ADR, mission direction, or project profile that defines success.
   - Extract success criteria and phase groups instead of relying only on the latest generated sequence map.

2. **Separate completion scopes**
   - Ladder state: current sequence, terminal summary, enabled/disabled flags, next-ladder.
   - Program state: mission status, runtime/scheduler health, stale signals, evidence overrides, adapter breadth, unattended/external actions, self-healing backlog.
   - Authority boundary: what remains fail-closed because it needs exact target, payload digest, rollback plan, blast-radius choice, or budget extension.

3. **Verify current evidence, not just old artifacts**
   - Read sequence-map and terminal-summary artifacts.
   - Read the live operator/control-plane snapshot when available.
   - Check mission board/doctor/signals for paused state, exhausted budget, open decisions, pending/stale signals, and cron runner health.
   - Re-run read-only projection/correlation/readiness/drift checks when the plan includes runtime or scheduler stability.
   - Run focused selfcheck/proof/eligibility checks when taskpool/control-plane health is in scope.

4. **Classify each remaining item**
   - `complete`: implemented, current, verified, and not only a packet/projection.
   - `terminal fail-closed`: intentionally no automatic next step; future work requires a new explicit gate.
   - `degraded-not-blocked`: usable but stale, partial, or awaiting natural observation/correlation.
   - `explicitly not implemented`: left out by design because it needs a consumption contract, broader adapter policy, external authority, or rollback semantics.

5. **Report accurately**
   - State which ladder is complete.
   - State which whole-program criteria remain partial, degraded, or authority-bound.
   - Do not invent a new phase when the sequence says none exists.
   - Do not equate read-only, packet-only, manual-only, or local-only closure with real external apply, unattended dispatch, or broad adapter support.

## Evidence bundle

Prefer a compact bundle with:

```text
sequence status / phase count / next-ladder / recommended next
terminal summary status / terminal state / enabled flags
live control-plane projection keys and status
mission board + doctor + signals
runtime projection / run correlation / readiness / drift status
selfcheck / proof-check / eligibility-check when applicable
scoped git status if code changed
```

## Pitfalls

- Treating a terminal ladder as whole-program completion.
- Treating a stage report as a wait point when the user authorized continuous progress; stage reports are checkpoints, not stops, unless a real boundary is reached.
- Treating a stage report as an execution wake signal; use the actual event/dispatch path for continuation.
- Ignoring mission-level state such as paused status, exhausted tick budget, or stale pending signals.
- Reporting old artifact health without checking whether runtime probes, gate artifacts, correlations, or receipt ledgers have gone stale.
- Calling packet-only/read-only/manual-only closure "done" when the target model required full write-through, external apply, or self-healing automation.

## Applicability and anti-conditions

Applicability: Hermes-owned mission, taskpool, Control Tower, workflow-kernel, and other governed control-plane ladders where terminal sequence evidence must be reconciled against a broader long-term plan.

Anti-conditions: do not use this review to reopen a closed ladder automatically. Budget expansion, external apply, publication, broader adapter mutation, unattended dispatch, and conflict-override consumption still require their own explicit authority gate and rollback/escape design.