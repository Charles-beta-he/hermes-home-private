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

Default stance: land what is safe, propose what needs governance, queue what needs execution, and explicitly refuse what would be authority expansion or false completion. A boundary is not a stop-work signal: after naming the blocked action, realign to the initial objective, continue safe read-only/reversible preparation, and emit the smallest required confirmation packet for the next gated step.

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
6. Freezing transient provider/auth failures into durable negative rules. If a multi-model run degrades because one provider/CLI was unauthenticated or stale, record the run as degraded/not-certified, but do not memorialize “provider X does not work.” When the user says the login/session was refreshed, re-probe the exact CLI/provider/model path first, then re-run the narrow model call or certification step and report the old blocker as resolved only if the probe returns real model output.

## Provider re-probe pattern for degraded multi-model reviews

Use this when a self-optimization or architecture review was degraded by provider authentication/runtime state and the user later says the provider login was fixed:

1. Preserve the original certification status: `degraded_not_certified` remains true for the old run; do not retroactively upgrade it.
2. Probe the exact runtime path that failed, preferably with a minimal sentinel response. Example shape: direct Hermes provider call with the same provider/model and a one-token/sentinel prompt.
3. Note provider/model normalization explicitly when relevant, because routing layers may normalize display names (for example dotted to dashed model aliases).
4. If the direct probe succeeds, run a narrow follow-up model call or re-certification and label it as a new evidence item, not as hidden repair of the old artifact.
5. Capture only the durable workflow: “re-probe exact provider path after auth refresh.” Do not save the transient auth failure itself as memory or as a standing tool limitation.

## Verification Checklist

- [ ] Each learning is classified as memory, skill, proposal, taskpool candidate, or do-not-do.
- [ ] Memory writes are durable, declarative, and not WIP/session progress.
- [ ] Skill changes have valid frontmatter and readable trigger/counter-trigger boundaries.
- [ ] Experience-ratchet atoms include evidence, applicability, anti-condition, and falsifier.
- [ ] Taskpool candidates include target, artifact, risk, dependencies, and verification.
- [ ] No external repo, release, credential, or destructive action was performed without explicit authorization.
- [ ] Changed Hermes artifacts were read back and committed with a scoped pathspec when git-managed.

## Timeout Escalation Ladder

Inspired by overmind's graceful-timeout-then-kill signal handling (command_go).
Multi-model reflections, boundary audits, and experience-ratchet proposals can
stall when models disagree or delegate chains recurse. Apply these guards:

| Threshold | Action | Rationale |
|---|---|---|
| Soft (120s) | Log a warning. Land whatever partial results exist as a taskpool candidate with `status: blocked` and `blocker_summary: "soft timeout — partial results landed"`. | Prevents silent drift; preserves work for human review. |
| Hard (300s) | Abort the operation. Commit any already-landed artifacts. Do not retry in this session. Emit `rollback_signal` if main_pass_rate degraded. | Mirrors overmind's graceful→force escalation; avoids indefinite hangs. |

When implementing timeout guards in scripts, prefer `signal.alarm` (Unix) or
`asyncio.wait_for` over polling loops. Always land partial results before
aborting — overmind's `command_go` temp-cleanup pattern (E-003) shows that
cleanup without landing loses observability.
