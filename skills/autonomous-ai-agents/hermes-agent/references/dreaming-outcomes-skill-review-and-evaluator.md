# Dreaming/Outcomes pattern for Hermes skill review and independent evaluator gates

Use this when converting a completed conversation, taskpool tranche, or complex agent run into durable Hermes operating knowledge without creating memory ghosts or self-approved closeout.

## Mechanism mapping

- Dreaming-style distillation = post-run conversion of repeated operational experience into a plain-text, executable procedure.
  - In Hermes this belongs in skills/references, taskpool proof logs, or sanitized brain docs.
  - It must not store raw session transcripts, raw MEMORY/USER dumps, credentials, or temporary task state.
- Outcomes-style separation = executor and evaluator are separate contexts with an explicit rubric.
  - The executor produces evidence and a claimed status.
  - The evaluator checks predeclared red lines, required fields, proof commands, residual risks, and whether the task may advance lifecycle.

## Trigger conditions

Create or patch a skill/reference only when at least one is true:
1. The same correction or workflow appeared in multiple sessions.
2. A task required 5+ tool calls or crossed context/permission boundaries.
3. A bug or governance failure was fixed in a way likely to recur.
4. A taskpool/autodone/proof gate needed a new invariant.
5. The user explicitly requested that a workflow be remembered or systematized.

Do not create skill material for one-off status, PR numbers, issue numbers, temporary task progress, or facts likely stale within a week.

## Distillation output template

Every Dreaming-style distillation should produce a short plain-text procedure with:

1. Trigger: when the agent should load/use it.
2. Preconditions: repo/path/config/authority checks needed before acting.
3. Steps: exact commands or tool surfaces, ordered.
4. Red lines: what must not be mutated, leaked, claimed, or closed.
5. Evidence: tests, command output, file paths, or proof rows required.
6. Verification: how to prove the change works now and on the next run.
7. Retirement: when this procedure becomes stale or upstream absorbs it.

## Independent evaluator rubric

For high-risk Hermes/taskpool closeout, a separate evaluator context should reject advancement unless all are true:

- Red lines respected: no credential leaks, no raw runtime state in code repo, no fake done/review, no unapproved push.
- Required task fields present: capability_delta, anti_drift_check, acceptance_evidence, proof/evidence rows, residual risk.
- Evidence is tool-backed: tests/selfcheck/logs/files were actually inspected, not asserted from memory.
- Lifecycle is honest: partial advisory progress returns to pending or review instead of done.
- Worker handoff is actionable: next actor can see context, commands, stop conditions, and exact boundary.
- Skill/memory distinction is correct: procedures go to skills; durable user/environment facts go to memory; session progress stays out of memory.

## Taskpool proof-gate integration

When applying this pattern to taskpool tasks:

1. Executor writes a bounded evidence tranche into the task note.
2. Executor adds structured evidence entries where supported, preferring `proof:` / `artifact:` / `classification:` prefixes.
3. Evaluator checks the task note against acceptance_evidence and red_lines.
4. If incomplete, release to `pending` with a reason and residual-risk handoff.
5. Only promote to review/done when lifecycle gate, proof gate, and required certification all pass.

## Minimal self-check command set

Use the smallest relevant set, then expand only if failures are found:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/post-update-check.py
```

For code-affecting changes, also run targeted tests and py_compile. For taskpool changes, verify row JSON, dispatch prompt, and handoff artifact surfaces.

## Common pitfalls

- Treating a summary as evidence. A summary is only evidence if it points to concrete commands/files/artifacts.
- Letting the same context that implemented a fix also certify `done` without a rubric.
- Writing ephemeral progress into memory instead of task notes or proof logs.
- Generating a skill from a single vague insight without trigger conditions.
- Auto-closing advisory multimodel PASS as if it were strong closeout certification.
