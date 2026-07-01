# Qianwen / AI Workflow and Local-Model Fallback Intake

Source boundary: user-shared Qianwen recording summaries from the same Agent-workflow learning thread. These are course/transcript-derived heuristics, not vendor documentation.

Scope: reusable Hermes-compatible Agent workflow and skill-authoring guidance across software projects.

Applicability: use when designing an AI-assisted development workflow, local/offline model fallback, feature/task decomposition, subagent/skill split, or review/verification loop.

Anti-conditions: do not use this as proof that a named vendor feature is currently available; do not bypass company security/model-use policy; do not auto-create external/cloud resources without explicit cost, permission, idempotency, and read-back gates.

Falsifier: revise if real projects show the proposed workflow contract, local-model fallback, or subagent/skill split reduces quality, speed, or verifiability.

## Transferable pattern additions

### 1. Model-availability resilience

Do not bind workflow capability to one frontier/vendor model.

If premium/cloud models are unavailable or policy-blocked, preserve the workflow shape and swap the execution lane:

- cloud/frontier model lane for high-reasoning orchestration when available;
- code-review/diff-specialist lane for review, legacy-code precision, and stuck repair;
- local model lane through an approved local runtime;
- browser-native model lane when the runtime exposes a local model API and capability has been verified;
- shell/JS/Python workflow runner lane when slash-command products are unavailable.

Key rule: the durable asset is the workflow contract, not the vendor UI.

### 2. Three-command workflow baseline

A simple, maintainable AI workflow can be represented as three stages:

```text
init  -> detect project architecture and write minimal project rules
prd   -> parse requirement source and split into feature folders
ai    -> execute feature/task loop with skills, review, tests, lesson writeback
```

Expected artifact structure:

```text
specs/
  feature-a/
    requirements.md
    design.md
    task.md
  feature-b/
    requirements.md
    design.md
    task.md
```

Keep project rules minimal; move role capability into skills and long references.

### 3. Feature / task granularity

Use human-work-sized chunks.

- Feature/Future: a cohesive deliverable or small requirement group.
- Task: a concrete implementation step.
- Preferred task count per feature: roughly 4-15; split if it grows too large.
- Avoid 100-task monoliths; large task lists cause context pollution, missed work, and hallucination.
- Encode task dependencies explicitly when parallelism is possible.

### 4. Context reset and lesson writeback

Long workflows must control context drift.

- After each task or small task group, clear/compress context before the next task where the tool supports it.
- Persist only reusable project lessons: pitfalls, API quirks, component conventions, generated abstractions, test learnings.
- Do not write transient progress as global memory.
- Project-level lesson files are acceptable when scoped to the repo/project and read deliberately by the workflow.

### 5. Requirement clarity is the highest-leverage bottleneck

AI coding quality is capped by requirement clarity.

- If requirements are unclear, use an Inversion/plan-grilling lane before implementation.
- Product-facing helpers should turn voice, screenshots, rough notes, or issue text into PRD-quality specs.
- Requirement clarification is not optional ceremony; it is the primary upstream quality gate.
- If humans cannot understand the requirement, do not expect the agent to implement it reliably.

### 6. SubAgent vs Skill split for full-stack automation

Use this split:

- SubAgent: role that owns a workstream and can load tools/skills, report, and coordinate. Examples: frontend engineer, backend engineer, data engineer, QA.
- Skill: bounded capability/checklist used by a role. Examples: security review, code style, UI component rules, database rules, testing checklist.

Create SubAgents for high-cohesion, parallelizable, implementation-heavy lanes.
Keep sequential gates and rubrics as skills.

### 7. Review modes and boundaries

Review is a bounded gate, not an infinite collaborator.

Review modes:

- Standard diff review — most common, checks current branch/change.
- Uncommitted/local review — checks worktree changes.
- Commit review — checks a specific commit or regression window.
- Adversarial review — high-cost, high-risk changes only; assumes failure until evidence disproves it.
- Repair lane — separate from review; use when the implementing agent is stuck.

Review should run after scoped task completion and before marking the task done. Add lint/type/test gates separately; do not rely on review prose alone.

### 8. Full-stack deployment closure

For AI-generated full-stack projects, closure requires more than code generation:

- architecture selected from PRD before implementation;
- frontend/backend/database/env contracts generated;
- local run or simulated environment verified;
- lint/type/test gates run where available;
- deployment target selected and verified;
- real endpoint/UI read-back captured;
- bug-tracker loop automated only after access, idempotency, and audit gates are defined.

### 9. Visual workflow UI is optional but useful

A workflow visualizer can help users understand progress, especially for non-engineers. It can be simple:

- nodes: init, PRD split, feature loop, task execution, review, test, deploy, lesson;
- roles: frontend/backend/data/QA;
- states: pending, running, blocked, review, passed, failed;
- event source: task manifest plus evidence ledger.

Do not make visualization a blocker for execution; it is an observability layer.

## Operational checklist

Before running an AI development workflow:

1. Resolve requirement source: PRD, voice transcript, URL, issue, screenshot, product note.
2. Convert weak requirements into structured PRD/spec first.
3. Run project architecture discovery.
4. Split into feature folders with requirements/design/task artifacts.
5. Choose execution lane: cloud model, local model, browser model, shell/JS runner, or hybrid.
6. Assign SubAgents only for parallel workstreams; use skills for sequential gates.
7. Execute tasks in small chunks.
8. Clear/compress context between chunks.
9. Run bounded review plus lint/type/test/browser/API verification.
10. Write project-scoped lessons only for reusable findings.
