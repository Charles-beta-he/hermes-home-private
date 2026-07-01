# Qianwen / Google Cloud Agent Workflow Intake

Source: user-shared Qianwen recording summary, `Google Cloud Agent设计模式与AI工作流实战指南`, accepted by the user for absorption.
Scope: reusable Agent Skill / workflow design heuristics. Do not treat course-specific tool claims as universal truth without current tool verification.

## Transferable pattern

The learning reinforces the existing five-pattern skill model:

1. Tool Wrapper — load framework/team/project knowledge only when triggered; keep long best practices in references rather than global prompts.
2. Generator — stabilize outputs through templates, required fields, missing-input handling, and structure checks.
3. Reviewer — review against an explicit checklist/rubric with severity, evidence anchors, and exit conditions.
4. Inversion — block guessing when requirements are underspecified; ask focused questions before design/implementation.
5. Pipeline — split complex work into gated stages where each stage has inputs, outputs, evidence, and rollback/retry behavior.

## Operational mapping

Use this mapping when designing Hermes/Claude/Codes-style Agent workflows:

- Main Agent: orchestration, task routing, gate decisions, final synthesis.
- SubAgent: role boundary, clean context, task execution, progress/report contract.
- Skill: concrete capability rules, references, templates, scripts, checklists.
- Workflow / JS script / hook: stage machine, dispatch policy, evidence ledger, retry/stop conditions.

Preferred chain for nontrivial work:

```text
Main Agent -> SubAgent role -> load relevant Skill -> produce/verifies artifact -> report evidence -> Main Agent gate
```

## Review loop boundary

Avoid unbounded AI-review-AI loops.

- One primary review pass is the default.
- Fix blockers and verify regressions.
- Re-review only scoped changed areas or unresolved blockers.
- Stop when acceptance criteria and evidence gates pass.
- Do not let stylistic suggestions repeatedly rewrite working code.

A Reviewer skill must distinguish:

- blocker: correctness, safety, missing requirement, failing verification;
- warning: likely maintainability/performance risk;
- suggestion: non-blocking style or alternative implementation.

## UI restoration / visual fidelity lane

For UI/design reconstruction tasks, treat visual parity as evidence-gated, not prose-gated.

Recommended flow:

1. Capture source of truth: Figma/MCP node, screenshot, exported HTML/CSS, or prototype.
2. Generate implementation using a precision-oriented model/tool lane when available.
3. Run browser screenshot verification.
4. Use visual diff tooling such as Backstop.js or equivalent screenshot diff when pixel parity matters.
5. Iterate only on measured diffs and acceptance criteria.

Do not claim UI completion from code inspection alone when the task is visual fidelity.

## Dynamic workflow / poor-man Ultra Code lane

When a single agent cannot reliably carry a large task:

- split by files/features/stages;
- keep each lane context-light;
- use a script or workflow runner to dispatch and aggregate;
- store stage evidence so the orchestrator can verify completion;
- cap concurrency and define retry/stop rules.

A JS/Python workflow plus hooks can approximate advanced dynamic workflow systems if it provides:

- task manifest;
- role dispatch;
- evidence collection;
- gate evaluation;
- resumability;
- final synthesis.

## Skill authoring implications

When writing or rehabilitating a skill, check:

- Is the dominant pattern explicit?
- Is long knowledge kept in `references/`?
- Does the root SKILL.md define routing and gates rather than become a giant README?
- Does a Generator have a template/schema?
- Does a Reviewer have rubric/severity/evidence?
- Does an Inversion skill identify non-defaultable questions?
- Does a Pipeline define no-skip stages and closure states?

## Anti-conditions

Do not apply this intake as:

- a mandate to create many tiny skills before every task;
- proof that any specific vendor feature is currently available;
- permission to run side-effecting automation without gates;
- a reason to skip real tests, browser screenshots, API read-back, or user acceptance.

## Falsifiers / update triggers

Revise this intake if:

- real skill audits show the five labels reduce routing precision;
- a workflow runner cannot preserve evidence/resumability;
- visual diff tooling adds more noise than signal for a specific UI class;
- current vendor tools change capability boundaries.
