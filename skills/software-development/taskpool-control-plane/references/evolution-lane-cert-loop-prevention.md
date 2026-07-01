# Evolution Lane Certification Loop Prevention

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Evolution Lane Certification Loop Prevention

See `references/evolution-lane-cert-loop-analysis.md` for full root cause analysis and prevention mechanisms.

Evolution lane tasks (exploratory: repo analysis, strategy design) are prone to `loop_non_convergence` deadlocks because models naturally disagree on approach/framing/implementation_order.

**Failure pattern:**
1. Task retries 2+ times → `loop_non_convergence` triggered
2. Certification requires `agreement_above_threshold(0.65)` on approach/framing/implementation
3. Exploratory tasks guarantee disagreement → `CONTINUE_LOOP` → infinite loop

**Root cause:** `brain_task_orchestrator.py` L1741: `if task.retry_count() >= 2: reasons.append("loop_non_convergence")`

**Prevention (when implementing):**
- Evolution lane: lower agreement threshold to 0.50 (delivery stays at 0.70)
- `amend` votes count as 0.7 weight (not 0.0 like reject)
- Max 3 certification rounds → auto `RATIFY_WITH_RESERVATIONS`
- Subtask completion → auto-trigger parent ratification
- `loop_non_convergence` trigger: `retry >= 3 AND no_progress` (not just `retry >= 2`)
