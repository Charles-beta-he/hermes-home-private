---
name: harness-intake-contract
description: "Use when converting vague work requests, social-media workflow lessons, taskpool items, pipeline envelopes, or mission slices into an executable AI-worker contract: map, goal, acceptance, division, evidence, and gates before automated execution."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    scope: cross-project-agent-workflow
    applicability: "Agent task intake, taskpool/pipeline/mission preparation, subagent delegation, and workflow-method absorption where execution needs map/goal/acceptance/evidence before worker action"
    anti_conditions: "Simple Q&A, trivial edits, pure media summaries without automation landing, or side-effecting production/destructive/secret/physical actions without a separate authority gate"
    tags: [harness, intake, taskpool, pipeline, acceptance, evidence, workflow]
    related_skills: [hermes-pipeline, taskpool-control-plane, objective-model-path-verification, goal-calibration, spec-stateful-sdd-workflow, subagent-driven-development]
---

# Harness Intake Contract

## Scope / Applicability / Anti-conditions

Scope: **cross-project agent workflow intake**.

Applicability: use when preparing AI-worker execution in taskpool, pipeline, mission, subagent delegation, or similar automation systems where the agent needs a clear map, goal, acceptance, division of labor, evidence shape, and gates before execution.

Anti-conditions:
- Do not use for simple Q&A, tiny edits, or one-command checks with obvious acceptance.
- Do not use for pure media summaries unless the user asks for workflow/automation absorption.
- Do not use this skill to bypass production, destructive, credential, external-delivery, payment, or physical-action authority gates.
- Do not treat social-media terminology as official evidence or as permission to rename existing architecture.

## Overview

Use this skill to turn an ambiguous request, social-media workflow lesson, taskpool row, mission slice, Lark task, GitHub issue, or pipeline envelope into a worker-ready contract. The contract exists so an AI worker can execute without guessing and a separate validator can decide completion without relying on optimistic prose.

Core formula:

```text
map + goal + acceptance + division + evidence + gates = automatable task unit
```

This is a Hermes-compatible adaptation of the useful part of Harness Engineering: define the environment, target, and proof conditions before asking agents to act. It is not a new model capability, not a plugin requirement, and not permission to bypass evidence, safety, or human gates.

## When to Use

Use this skill when:

- A request is about task automation, AI worker orchestration, taskpool, pipeline, mission advancement, or subagent delegation.
- A task is phrased vaguely: “做一下 / 优化 / 推进 / 修复 / 对齐 / 全盘推进” and needs executable acceptance.
- A social/video/article claims a workflow improvement such as Harness Engineering, Context Engineering, Loop Engineering, Agentic Engineering, or AI-worker orchestration and the user wants automation absorption.
- A taskpool item or pipeline envelope is about to enter executor/worker mode but lacks map, goal, acceptance, or proof requirements.
- You need to separate executor work from validator/reviewer work to avoid the worker being both athlete and referee.

Do not use this skill for:

- Simple Q&A or one-command checks with an obvious answer.
- Pure media summaries where no task automation landing is requested.
- Runtime/code changes that already have a more specific implementation skill and complete acceptance criteria.
- External side effects, production promotion, secret handling, payments, destructive cleanup, or physical actions without the relevant authority gate.

## Intake Contract Schema

Use this shape as the default contract. Omit only fields that are genuinely irrelevant; do not omit acceptance or evidence for executable work.

```yaml
map:
  project_purpose: "What this system/repo/task is for"
  state_source: "project profile | AGENTS.md | repo docs | taskpool record | mission ledger | user-provided context"
  repo_or_surface: "target path/app/API/dashboard, if any"
  key_files_or_objects: []
  existing_conventions: []
  forbidden_changes: []

goal:
  user_intent: "plain-language desired outcome"
  desired_state: "observable end state"
  non_goals: []
  constraints: []
  assumptions: []

acceptance:
  observable_results: []
  required_commands: []
  required_artifacts: []
  screenshots_or_logs: []
  precision_rules: []
  regression_boundaries: []

division:
  executor_role: "implementer | researcher | operator | reviewer-only"
  validator_role: "independent review criteria"
  subagents: []
  conflict_groups: []
  ownership_boundary: "who may mutate what"

evidence:
  proof_schema: "freeform | PROOF_JSON | command/log/screenshot/file/readback"
  evidence_refs: []
  minimum_done_proof: []
  readback_required: true

gates:
  risk_level: "low | medium | high"
  human_gate_required: false
  human_gate_reason: ""
  side_effects_allowed: []
  dry_run_first: true
  rollback_or_escape: ""
```

## Default Workflow

### 1. Resolve the map before execution

Find the authoritative context before letting a worker act:

- Project-specific durable facts: project profile or repo docs.
- Repo-local conventions: `AGENTS.md`, `CLAUDE.md`, package scripts, tests, existing patterns.
- Agent self-architecture: relevant workflow skill/reference, taskpool record, mission ledger, or canonical design note.
- User-provided artifact: URL/page metadata/video transcript/screenshots, then direct source verification when claims mention external repos/products.

If multiple surfaces could be targets, resolve the target artifact/path before editing.

### 2. Convert intent into a desired state

Rewrite vague verbs into an observable target:

- “优化” → what metric, behavior, or risk improves?
- “对齐” → align with which source and which differences matter?
- “修复” → reproduce or identify root cause, then expected behavior.
- “全盘推进” → continue safe reversible slices until a real authority/evidence/safety gate appears.

Name non-goals explicitly. This prevents workers from deleting features, changing unrelated architecture, or interpreting a demo as permission to rewrite systems.

### 3. Write acceptance before worker execution

Acceptance must be checkable by someone who did not perform the work. Prefer concrete commands, files, screenshots, HTTP responses, diff boundaries, or proof JSON. For UI work, include real browser/viewport evidence; mock-only evidence is not completion. For data/entity/API changes, include migration/schema/backward-compatibility checks. For agent self-changes, include skill/readback, focused tests, local guard commands when relevant, and scoped commit boundaries.

### 4. Split executor from validator

Default split:

```text
confirmer/intake: complete the contract
executor: perform only the authorized implementation/research/operator action
validator: independently check acceptance and evidence
reporter: summarize evidence, boundary stops, and next gates
```

For low-risk tasks, executor self-review can be accepted only if proof is deterministic and easy to inspect. For medium/high-risk tasks, use an independent reviewer/subagent/model or deterministic validation command.

### 5. Classify gates before side effects

Stop or dry-run first when the next action crosses any of these boundaries:

- production promotion, deploy, push, publish, payment, external delivery;
- credentials/secrets/API keys/passwords;
- destructive delete, irreversible migration, broad cleanup;
- physical-world control or device actuation;
- value judgment or product/architecture fork not determined by the user;
- evidence insufficiency that changes implementation path.

Continue safe read-only, local, reversible, patch-preparation, rollback-design, and verification work while waiting for the gate.

## Taskpool / Pipeline Mapping

Map the contract into agent workflow surfaces like this:

```text
map.state_source          -> project profile / AGENTS.md / taskpool evidence_refs / mission ledger
goal.user_intent          -> task body / envelope summary
goal.non_goals            -> task non_goals / red_lines
acceptance.*              -> acceptance_criteria / workflow_contract / validator prompt
division.executor_role    -> worker prompt / model route / toolsets
division.validator_role   -> validator prompt / review lane / proof gate
evidence.minimum_done     -> proof requirements / PROOF_JSON / command evidence
gates.*                   -> human escape / risk tier / dry-run / side-effect policy
```

For pipeline execution, the confirmer should output the contract JSON and only then build the executor prompt. For taskpool execution, missing acceptance or proof requirements should block direct autorun and trigger contract completion rather than letting a worker guess.

## Social-Video / External-Workflow Absorption

When the source is a short video or social post:

1. Resolve the canonical URL and capture page metadata/transcript/chapters.
2. Separate the creator's claims from directly verified artifacts.
3. Classify the content:
   - vocabulary/checklist lesson;
   - reusable workflow contract;
   - actual tool/repo/package to evaluate;
   - architecture pattern needing a guarded reference review.
4. Land vocabulary/checklist lessons as a skill or reference only when they produce executable checks.
5. Do not rename existing architecture because a term is trending.
6. Do not import plugins/repos or mutate runtime from a social clip alone.

## Output Forms

### Compact contract

```text
目标: ...
地图: source/path/key facts
验收: commands/artifacts/proof
分工: executor vs validator
门禁: allowed side effects / stop point
```

### Worker prompt skeleton

```text
You are the executor. Use the map below as constraints, implement only the goal, respect non-goals and forbidden changes, then produce proof.

MAP: ...
GOAL: ...
NON-GOALS / RED LINES: ...
ACCEPTANCE: ...
AUTHORIZED TOOLS/SIDE EFFECTS: ...
REQUIRED PROOF: ...
```

### Validator prompt skeleton

```text
You are the independent validator. Do not assume executor success. Check the artifacts and evidence against acceptance. Return pass/warn/reject with missing evidence and exact next action.

CONTRACT: ...
EXECUTOR OUTPUT / DIFF / LOGS: ...
EVIDENCE: ...
```

## Positive Trigger Evals

These prompts should load this skill:

1. “这个视频讲 Harness Engineering，吸收到任务自动推进里，全盘推进。”
2. “把这个 Lark 任务转成可以让 agent team 自动执行的任务单。”
3. “taskpool 里这个任务一直 done 不了，先补齐目标、验收、proof 再跑 worker。”

## Neighbor / Negative Evals

These prompts should not load this skill as the primary workflow:

1. “总结这个抖音视频讲了什么” — use media/social analysis unless the user asks for automation landing.
2. “修复这个具体 TypeScript 编译错误，测试已经给了” — use systematic debugging / TDD / project-specific implementation skills; this skill is unnecessary unless acceptance is missing.
3. “把文件改个错别字” — direct edit; no harness ceremony needed.

## Common Pitfalls

1. **Vocabulary trap:** treating Harness/Context/Loop Engineering labels as proof of new capability. Extract executable checks instead.
2. **Map-only trap:** adding AGENTS.md/context but no acceptance means workers still guess done state.
3. **Acceptance-after trap:** writing tests/proof only after implementation lets the worker define its own finish line.
4. **Athlete-referee trap:** relying on executor's confident summary instead of independent evidence or deterministic commands.
5. **Over-ceremony trap:** applying the full contract to tiny obvious tasks wastes budget; use the compact form or skip.
6. **Authority creep:** “全盘推进” authorizes safe reversible progress, not production push, destructive cleanup, secret handling, or external side effects.
7. **Social-proof trap:** a short clip is intake evidence, not official documentation or runtime validation.

## Verification Checklist

- [ ] The target surface and source of truth were identified before execution.
- [ ] Goal, non-goals, constraints, and assumptions are explicit.
- [ ] Acceptance is concrete enough for an independent validator.
- [ ] Required proof/evidence shape is named before worker execution.
- [ ] Executor and validator roles are separated or self-review is justified by deterministic evidence.
- [ ] Human gates and allowed side effects are explicit.
- [ ] If landed into taskpool/pipeline, the contract fields map to task/envelope/proof fields.
- [ ] If derived from social media, creator claims are separated from verified artifacts.
