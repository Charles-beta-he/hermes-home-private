---
name: hermes-personal-assistant-flow
description: "Use when turning a human request into a Hermes personal-assistant workflow: intake, goal calibration, evidence-first routing, taskpool/delegation/cron selection, verification, handoff, and reusable experience capture."
---

# Hermes Personal Assistant Flow

## Overview

Use when turning a human request into a Hermes personal-assistant workflow: intake, goal calibration, evidence-first routing, taskpool/delegation/cron selection, verification, handoff, and reusable experience capture. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to Use

Use this skill when the request matches the `hermes-personal-assistant-flow` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use this skill when the user asks Hermes to act as a personal assistant, create an assistant workflow, close a loop across tools/projects, or convert an ambiguous request into durable execution.

Reference: `references/agent-productization-and-independent-delivery.md` covers the class-level path from business scenario to agent/personal-assistant deliverable: Hermes-native MVP, Hermes-incubated independent agent, or reusable agent runtime/product base, with workflow pack, evidence, human gates, and extraction mapping.

## Operating principles

- Evidence first: gather local/project/session/tool context before making claims.
- Goal calibration first for vague or prompt-like requests: infer the durable target, ask only when ambiguity changes execution.
- No fake completion: every closure needs proof from commands, UI screenshots, API responses, files, logs, or taskpool evidence.
- Keep state in the right place:
  - Memory: durable user/environment facts only.
  - Skills: reusable procedures.
  - Taskpool/Kanban: resumable work and dependencies.
  - Cron: scheduled or repeated autonomous checks.
  - Session search: past conversation recall.
- Prefer production-long-term solutions over one-off patches unless the user explicitly asks for a quick throwaway.

## Default flow

1. Intake
   - Identify request type: quick answer, research, project work, Hermes operation, personal scheduling/reporting, automation, or external-control action.
   - Identify target object: project/repo/profile/channel/device/service.
   - If the target is a concrete project, run project preflight: profile, repo instructions, and workpad/handoff context when available.

2. Goal calibration
   - Build an internal TaskContract:
     - user_goal
     - task_type
     - baseline/current state
     - success_criteria
     - constraints/red lines
     - ambiguity_level
     - execution_mode
   - Ask a question only when two reasonable interpretations would lead to different side effects or deliverables.

3. Context and evidence gathering
   - Use session_search for “之前/上次/我们做过什么” style references.
   - Use filesystem/git/browser/API tools for current state.
   - For current time, math, versions, system state, and git history, always use tools.
   - For Hermes itself, load `hermes-agent` and inspect state before modifying.

4. Route execution
   - Single-step, low-risk task: act directly.
   - Multi-step coding/project task: make a small plan, then implement in verifiable slices.
   - Parallel research/review: delegate independent branches to subagents, then verify their claimed artifacts.
   - Long-running or resumable work: create taskpool/Kanban entries with order, dependencies, acceptance criteria, red lines, and evidence refs.
   - Repeated scheduled work: create a cron job with a self-contained prompt; do not rely on current chat context.
   - External side effects: verify target and require appropriate confirmation when the action is risky or irreversible.

5. Execute
   - Keep one active work item at a time in the visible todo list when the task has 3+ steps.
   - Before editing code, fetch/pull when applicable and inspect current diffs.
   - Apply the smallest sufficient change unless the user explicitly asks for architecture/refactor scope.
   - Do not remove features, fields, routes, or entries unless explicitly intended and verified.

6. Verify
   - Match verification to task type:
     - Code: tests, build, lint/typecheck, focused runtime checks.
     - UI: real backend/auth/session when required; screenshots or browser harness evidence.
     - Hermes: `hermes --version`, git status, post-update checks, relevant script smoke tests.
     - Cron/taskpool: list jobs/tasks, status, logs, and dry-run/proof output.
   - If verification cannot be completed, state exactly what is unverified and why.

7. Handoff and closure
   - Report only: what changed, where, proof, leftovers, and next action if any.
   - For queued work, include dependency/order and acceptance criteria.
   - For files changed, state absolute path or repo-relative path as appropriate.
   - For commits made, include commit hash only when actually committed.

8. Experience capture
   - Save durable preferences/facts to memory only if they will remain useful across sessions.
   - Create or patch a skill for reusable procedures discovered through non-trivial work.
   - Do not save temporary task progress, PR numbers, issue numbers, commit SHAs, or “done” logs to memory.

## Personal-assistant workflow templates

### A. Quick execution

1. Parse target and success condition.
2. Use the minimum required tool for grounding.
3. Act.
4. Verify.
5. Return concise result plus evidence.

### B. Project delivery

1. Resolve project profile and repo context.
2. Pull/fetch if code will be modified.
3. Inspect related FE/BE/contract/infrastructure surfaces.
4. Implement small slice.
5. Run focused tests/builds.
6. Browser/API verify against real environment when required.
7. Handoff with changed files and proof.

### C. Taskpool creation

Each task should include:

- Title
- Priority: P1/P2/P3
- Sequence/dependencies
- Scope
- Acceptance criteria
- Red lines/non-goals
- Evidence required for done
- Suggested execution lane/model, if relevant

### D. Scheduled assistant flow

For cron jobs, prompt must be self-contained:

- Objective
- Data sources/tools to inspect
- Conditions for sending a message
- Output format
- Failure behavior
- Whether silence is acceptable when no update exists

## Pitfalls

- Do not treat a plan as completion.
- Do not infer current project/system state from memory.
- Do not enqueue vague tasks without acceptance criteria and evidence gates.
- Do not let subagent self-reports become final proof; verify returned files/URLs/statuses.
- Do not create recurring jobs that depend on unstated chat context.
- Do not write stale task progress into memory.

## Verification checklist

Before final response, confirm:

- The user’s actual goal was satisfied or the remaining gap is explicit.
- All factual claims are backed by provided context or tool output.
- Side effects are scoped and intentional.
- Verification evidence is included.
- Reusable lessons were saved to a skill, not memory, when appropriate.
