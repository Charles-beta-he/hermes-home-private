# Agent Skill Pattern Matrix

Scope: reusable Agent Skill authoring and audit work.

Applicability: use as a compact comparison when classifying or refactoring a skill.

Anti-condition: do not use this matrix as a rigid ontology; adjacent modes may dominate.

| Pattern | Core question | Primary artifact | Root SKILL.md must emphasize | Support files usually hold | Verification |
|---|---|---|---|---|---|
| Wrapper | What external capability is safely exposed? | command/API result, external state, config | preconditions, invocation contract, safety gates, read-back | API docs, command references, helper scripts | exit code + target state read-back |
| Generator | What stable artifact is produced? | doc, code, config, spec, report, diagram | input schema, output contract, template/quality bar | templates, examples, schemas | schema/template/build/test/read-back |
| Reviewer | What is judged and by what rubric? | findings, severity, pass/warn/fail | review dimensions, severity, evidence rules | detailed checklists, examples, golden defects | evidence citations + severity calibration |
| Inversion | What control/constraint must drive the agent before acting? | questions, spec, decision log, falsifiers | minimal questions, defaultable vs blocking unknowns, stop conditions | interview guides, domain background | no-unnecessary-question + answer-to-spec coverage |
| Pipeline | What stages must advance with gates? | stage outputs, evidence ledger, closure state | stages, gates, evidence, rollback, closure | detailed commands, templates, scripts | stage postconditions + E2E trace |

## Adjacent dominant modes

Use these as primary only when they are the actual main behavior:

| Adjacent mode | Dominant behavior | Common combination |
|---|---|---|
| Router / Dispatcher | selects skill/tool/model/subagent | wraps all five patterns |
| Planner / Decomposer | decomposes goal and dependencies | precedes Pipeline |
| Memory / Retrieval | selects and compresses context | supports Generator/Reviewer/Pipeline |
| Monitor / Watchdog | observes events/thresholds | Wrapper + Inversion + Pipeline |
| Guardrail / Policy | enforces permission/safety | stricter Reviewer |
| Arbiter / Consensus | resolves conflicting reviews/opinions | Reviewer specialization |
| Evaluator / Benchmark | tests skill behavior over cases | governs all patterns |

## Fast smell checks

- Wrapper without read-back is unsafe.
- Generator without output contract is unstable.
- Reviewer without evidence/severity is opinion.
- Inversion without stop conditions is annoyance.
- Pipeline without gates is a checklist.
