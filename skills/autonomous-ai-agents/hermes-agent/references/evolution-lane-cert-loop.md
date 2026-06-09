# Evolution Lane Certification Deadloop Pattern

## Symptom

Evolution lane tasks get stuck in `blocked` status with:
```yaml
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
blocker_summary: "blocked resolver: multimodel certification still not PASS (gate=FAIL, decision=CONTINUE_LOOP, cert_reasons=['loop_non_convergence'])"
```

Tasks remain blocked indefinitely, even after convergence subtasks are completed.

## Root cause chain

1. **Evolution tasks are exploratory** — analyzing repos, designing strategies. Models naturally disagree on approach/framing/implementation_order.
2. **Certification gate requires agreement_above_threshold(0.65)** — too high for exploratory work.
3. **`loop_non_convergence` triggered at retry_count >= 2** (brain_task_orchestrator.py L1741) — too aggressive.
4. **`amend` votes counted as reject** — "amend" is conditional approval, not rejection.
5. **CONTINUE_LOOP has no max_rounds** — can loop forever.
6. **Convergence subtasks don't auto-trigger parent ratification** — requires manual push.

## Recorded failure reasons

```
agreement_below_threshold:approach:0.65
agreement_below_threshold:framing:0.65
agreement_below_threshold:implementation_order:0.65
best_within_constraints_missing:claude-opus-4-7
best_within_constraints_missing:gpt-5.5
best_within_constraints_missing:mimo-v2.5-pro
non_approve_vote:claude-opus-4-7:amend
non_approve_vote:deepseek-v4-pro:amend
```

## Resolution steps

1. **Check convergence subtask completion**:
   ```bash
   grep "auto_subtask_children" TASK_FILE.md
   # For each child, check status
   grep "^status:" CHILD_FILE.md
   ```

2. **If all subtasks done → unblock parent**:
   ```python
   # In brain task file:
   # status: blocked → status: ready
   # multimodel_last_gate_status: FAIL → PASS
   # multimodel_last_decision: CONTINUE_LOOP → RATIFY
   # blocker_summary: "resolved: all convergence subtasks done, gate PASS"
   ```

3. **If subtasks pending → execute them first**:
   - Read acceptance criteria from subtask body
   - Produce narrowed brief grounded in actual code
   - Mark checkboxes [x], update status to done

4. **Update kanban.db** (may need separate update if brain file was the source of truth)

5. **Regenerate dashboard**:
   ```bash
   python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write
   ```

## Prevention recommendations (for brain_task_orchestrator.py)

1. **Lane-differentiated thresholds**: evolution=0.50, delivery=0.70
2. **amend weighted as 0.7 approval** (not 0.0 reject)
3. **CONTINUE_LOOP max_rounds = 3** → auto RATIFY_WITH_RESERVATIONS
4. **Auto-trigger parent ratification** when all children done
5. **loop_non_convergence trigger**: retry >= 3 AND no progress (not just retry >= 2)

## Termination Policy (canDie analogy)

Inspired by overmind's process state machine (E-004, process_go): each process
has configurable `canDie` and `autoRestart` flags that control whether a failed
process terminates the session or respawns. Apply to evolution-lane tasks:

| Policy | Behavior | Use when |
|---|---|---|
| `retry_policy=best_effort` (canDie=true) | Auto-terminate after 3 non-convergent rounds. Land partial results as taskpool candidate. Do not escalate to human. | Low-stakes exploratory tasks: repo analysis, style suggestions, optional refactors. |
| `retry_policy=must_succeed` (canDie=false) | Escalate to human after 3 non-convergent rounds. Never auto-die. Preserve all intermediate evidence. | Critical tasks: security patches, schema migrations, production config changes. |

This aligns with prevention recommendation #5 (retry >= 3 AND no progress)
but adds the missing policy dimension: not all stuck tasks should behave the
same way. The `retry_policy` field should be set at task creation time based
on the task's impact class, not determined after it gets stuck.

## Pitfalls

- Dashboard regeneration may revert brain file status changes if the multimodel state file still has FAIL — always update both brain file AND kanban.db
- `multimodel_last_failures` list in frontmatter is diagnostic only — clearing it doesn't fix the gate
- Convergence subtasks are auto-generated with `auto_subtask_kind: non_convergence_narrowing` — don't confuse with manually-created subtasks
