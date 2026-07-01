# Qianwen / Swarm, Adaptive Router, Workflow DSL Intake

Source boundary: user-shared Qianwen recording summaries from the Agent-workflow learning thread. The two provided links resolved to the same Qianwen recording content/title in the browser capture: `AI自动化工作流设计与Swarm架构解析`.

Scope: reusable Hermes-compatible Agent workflow design guidance for multi-agent orchestration, adaptive routing, workflow DSLs, learning loops, and safety gates.

Applicability: use when designing a workflow router, multi-agent lane, code-review arbitration, task-memory/lesson retrieval, or JavaScript/Python workflow runner that emulates higher-end dynamic workflow products.

Anti-conditions: do not treat third-party product marketing claims as verified capability; do not add cross-machine/federated execution before local single-machine workflow is stable; do not send secrets, PII, customer data, or proprietary context across agent/tool boundaries without explicit redaction, policy, permission, and audit gates.

Falsifier: revise if flat SubAgent+Skill orchestration fails to scale, if adaptive routing misclassifies cost/complexity, or if lesson retrieval introduces stale/incorrect context more often than it prevents repeated mistakes.

## Transferable mechanisms

### 1. Swarm as flat role team, not deep hierarchy

Use Swarm as a practical metaphor for a temporary project team:

- Leader/Main Agent: routes, gates, summarizes, arbitrates.
- SubAgents: role-specific work lanes such as frontend, backend, data, QA, security.
- Skills: concrete rules/checklists/templates loaded by roles.

Prefer a flat topology:

```text
Main Agent -> SubAgent(s) -> Skill(s)
```

Avoid deep chains like `agent -> subagent -> sub-subagent -> sub-sub-subagent` unless there is evidence the coordination cost is worth it.

### 2. Adaptive router by feature/task complexity

Route each feature/task, not only the whole project.

Suggested lanes:

- Low complexity: ordinary model/direct execution with standard verification.
- Medium complexity: normal feature/task workflow with skills, review, tests, and context reset.
- Medium-high complexity: add goal/finish-condition loop or stronger review gates.
- Very high complexity: dynamic workflow lane with multiple isolated agents, architecture map, adversarial verification, and final synthesis.

Router inputs:

- feature/task size;
- number of files/modules affected;
- dependency graph width;
- risk: auth, money, data, security, migration, deployment;
- ambiguity level;
- prior lessons retrieved for this area;
- deadline/cost constraints.

### 3. Judgement separation and orchestration separation

Two useful separations:

- Judgement separation: the worker that creates the artifact should not be the only judge of completion. Use an independent reviewer/checker or deterministic test gate.
- Orchestration separation: large tasks should not rely on one context window to remember everything. Use stage runners, subagents, task manifests, evidence ledgers, and synthesis.

This generalizes beyond any single vendor feature.

### 4. Adversarial verification lane

For high-risk outputs, use independent verification:

- Generator produces artifact.
- Skeptic/reviewer gets no authorial bias and tries to disprove or find failure modes.
- Reviewer must cite evidence: files, lines, API responses, screenshots, logs, tests.
- Final arbiter resolves findings against acceptance criteria.

Use sparingly because adversarial lanes are expensive.

### 5. Learning loop / lesson retrieval

A workflow should learn from completed work, but only with scoped, reusable lessons.

Minimum viable learning loop:

```text
Task result -> extract reusable lesson -> store project-scoped lesson -> retrieve by feature/task keywords next time -> inject only relevant lesson -> verify it still applies
```

Do not store task progress as lessons. Store:

- recurring pitfalls;
- project conventions;
- API/SDK quirks;
- component abstraction decisions;
- environment/deployment gotchas;
- verification patterns.

Future upgrade path: Markdown lessons first; vector/embedding retrieval only after provenance, drift, deletion, and relevance gates are defined.

### 6. PII/secret outbound filter

Any workflow that sends context outside the local process or trusted project boundary needs outbound filtering.

Filter classes:

- secrets: API keys, tokens, passwords, private keys;
- PII: identity numbers, phones, emails, addresses, customer identifiers;
- proprietary data: internal URLs, customer names, financial records, unreleased business data;
- high-risk operational data: prod credentials, deployment targets, incident details.

Outbound rule:

```text
Before external agent/tool/model call -> classify payload -> redact/deny/ask -> log decision -> send minimal necessary context
```

Local same-process skill calls may not need the same gate, but external tools, cloud models, cross-machine agents, ticketing systems, email, and chat do.

### 7. Conflict arbitration

When agents disagree, avoid majority voting as the default. Prefer evidence-ranked arbitration:

1. Deterministic tests / typecheck / lint / API read-back.
2. Security or data-integrity gate for high-risk changes.
3. Specialist reviewer with source evidence.
4. Main Agent decision with stated assumptions.
5. Human gate for irreversible, costly, external, or ambiguous decisions.

If a code-review specialist is the configured arbiter, treat it as advisory unless supported by evidence or deterministic gates.

### 8. Workflow DSL / runner abstraction

Higher-end dynamic workflows often look like a DSL with primitives such as:

- `agent(role, task, context)`;
- `pipeline(stages)`;
- `parallel(tasks)`;
- `stage(name)`;
- `verify(candidate, rubric)`;
- `synthesize(results)`.

The exact vendor runtime may be inaccessible, but the abstraction is reproducible with JS/Python runner plus Hermes/delegate tools.

A local runner should provide:

- task manifest;
- role prompts and skill references;
- parallel dispatch with concurrency cap;
- evidence ledger;
- verification stages;
- redaction gate;
- resumability;
- final synthesis.

### 9. Project-owned workflow, not person-owned ritual

Workflow should follow project/type-of-project, not individual habit.

- Store workflow assets in the project or approved shared workspace.
- Each project/domain can have its own skills and gates.
- Team members contribute skills/lessons from their expertise.
- One workflow can run on a dedicated machine/server, but ownership and evidence must be visible.
- Human value shifts toward understanding business, requirements, architecture, verification, and workflow design.

## Operational checklist

When upgrading a simple MD workflow into a Swarm/router workflow:

1. Keep current simple flow working first.
2. Add router at feature/task boundary, not just global entry.
3. Define low/medium/high complexity thresholds.
4. Keep SubAgent topology flat.
5. Add bounded adversarial verification only for high-risk lanes.
6. Add learning-loop writeback with scope and anti-stale checks.
7. Add outbound PII/secret filtering before external calls.
8. Add evidence-ranked arbitration for agent conflicts.
9. Use JS/Python workflow DSL only where MD/slash-command workflow becomes too brittle.
10. Verify with a real project slice before promoting the workflow as reusable.
