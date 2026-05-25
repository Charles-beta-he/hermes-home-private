---
name: agent-boundary-audit
description: Use when a user asks for self-optimization, multi-model reflection, experience landing, or "落地到边界"; classify conclusions into memory, skill, experience-ratchet proposal, taskpool candidate, and prohibited action before claiming completion.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [self-optimization, boundary, ratchet, memory, skills, taskpool]
    related_skills: [hermes-agent, hermes-experience-ratchet, experience-ratchet, multi-agent-code-review]
---

# Agent Boundary Audit

## Overview

Use this skill when a result should be learned by Hermes itself without overstepping authority. The goal is to turn multi-model reflections, repo-governance lessons, or user corrections into the right durable landing zone while preserving evidence, permission, and reversibility.

Default stance: land what is safe, propose what needs governance, queue what needs execution, and explicitly refuse what would be authority expansion or false completion.

## When to Use

- The user says: 自我优化, 多模型思考, 自身可学习, 经验沉淀, 全盘落地, 落地至边界.
- A multi-model review produced reusable methodology rather than a one-off answer.
- A session reveals a durable assistant behavior correction or workflow improvement.
- You are tempted to write memory, create/patch skills, enqueue taskpool work, or change Hermes defaults from one discussion.

Don't use for:
- Simple factual answers with no durable workflow implication.
- Project-specific implementation details that belong in a project profile or Workpad.
- Active task progress, PR numbers, issue numbers, or other stale session status.

## Boundary Classifier

| Landing zone | Write when | Do not write when | Required proof |
|---|---|---|---|
| `memory` | Stable user preference, environment fact, or recurring correction that remains useful across many sessions | WIP status, one-off repo facts, legal conclusions, secrets, task progress | User statement or repeated correction; compact declarative wording |
| `skill` | Reusable procedure with trigger, ordered steps, pitfalls, and verification | One-off advice, broad ideology, project-specific rule, or unverified claim | Skill read-back/validation; frontmatter; trigger/counter-trigger clarity |
| `experience-ratchet proposal` | Cross-project or default-behavior change needing review before promotion | Anything requiring direct immediate behavior change without review | Atom with evidence, applicability, anti-condition, falsifier, dissent |
| `taskpool candidate` | Concrete future engineering work that needs scope, permissions, cost, or repo context | Vague improvement desire or already-completed action | Target, expected artifact, risk, dependencies, verification standard |
| `do-not-do` | Action would expand authority, weaken gates, claim unverified success, leak secrets, or mutate external systems | N/A | Explicit refusal or boundary note |

## Workflow

1. Gather evidence first.
   - For multi-model requests, use real external models when available; label failures and fallbacks.
   - Separate evidence from model opinions; multi-model agreement is not truth.
2. Build the boundary table.
   - List candidate learnings and assign exactly one primary landing zone.
   - If a conclusion spans zones, split it into smaller claims.
3. Land low-risk durable facts.
   - Write memory only for stable user/environment facts.
   - If memory is full, replace a broader or stale entry rather than appending blindly.
4. Land reusable procedure.
   - Prefer patching an existing skill; create a new skill only for a distinct trigger class.
   - Include triggers, counter-triggers, steps, pitfalls, and verification.
5. Capture governance-level claims as experience-ratchet atoms.
   - Include applies/anti/falsifier/evidence/dissent.
   - Use `propose` to emit proposal artifacts; do not directly mutate Hermes core from the overlay.
6. Treat larger work as taskpool candidates.
   - Do not enqueue unless the user asked for future execution or the task is already within the current authorized scope.
   - Candidate format: title, dependency order, expected artifact, risk, verification.
7. Verify and commit scoped Hermes changes.
   - Read back created/changed skill artifacts.
   - Run available validation commands for experience-ratchet artifacts.
   - For changes under `~/.hermes`, make a scoped git commit with only the files changed for this landing.

## Output Template

```text
边界落地结果：
- memory: <written/replaced/skipped + reason>
- skill: <path + validation>
- experience-ratchet: <atom/proposal ids>
- taskpool candidates: <queued/skipped + candidate list>
- do-not-do: <explicit boundaries>
- verification: <commands/files read back>
- commit: <sha or why not committed>
```

## Common Pitfalls

1. Treating multi-model consensus as permission to change global behavior. Consensus can justify a proposal; it is not a truth gate or authorization gate.
2. Writing a memory for a temporary repo observation. External repo facts and session outcomes go to evidence/proposals, not user memory.
3. Creating broad skills for one-off advice. Patch an existing umbrella or create a narrow trigger-class skill with negative space.
4. Enqueuing noisy taskpool work from every insight. Only queue concrete work with target, artifact, risk, and verification.
5. Claiming the landing is complete without reading back the artifacts and checking git scope.

## Verification Checklist

- [ ] Each learning is classified as memory, skill, proposal, taskpool candidate, or do-not-do.
- [ ] Memory writes are durable, declarative, and not WIP/session progress.
- [ ] Skill changes have valid frontmatter and readable trigger/counter-trigger boundaries.
- [ ] Experience-ratchet atoms include evidence, applicability, anti-condition, and falsifier.
- [ ] Taskpool candidates include target, artifact, risk, dependencies, and verification.
- [ ] No external repo, release, credential, or destructive action was performed without explicit authorization.
- [ ] Changed Hermes artifacts were read back and committed with a scoped pathspec when git-managed.
