---
name: context-engineering-os
description: "Use when turning Context Engineering into an agent/workflow operating system: assemble objective, evidence, memory, skills, project state, tools, authority, execution, and verification into a minimal sufficient context packet."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [context-engineering, agents, memory, rag, evidence, workflow, verification]
    related_skills: [objective-model-path-verification, abstraction-governance, project-evidence-grounding, taskpool-control-plane, spec-stateful-sdd-workflow]
---

# Context Engineering OS

## Overview

Context Engineering is the discipline of designing the full information payload an LLM/agent receives at inference time. It is broader than prompt wording: it covers objective framing, source/evidence selection, retrieval, memory, project state, tool schemas, authority boundaries, execution observations, and verification feedback.

Use this skill to turn a vague "add more context" instinct into a governed Context Packet and Evidence DAG. The goal is minimal sufficient context: enough to act correctly, not so much that stale, irrelevant, or unauthorized state pollutes the run.

## When to Use

Use when:
- The user asks about Context Engineering, agent memory, RAG, long-context agents, or AI coding reliability.
- A complex task needs multiple source types: docs, code, screenshots, session history, project profiles, skills, tools, logs, API readbacks.
- Agent failures appear caused by missing, stale, noisy, or incorrectly scoped context.
- You need to design a workflow/runtime that coordinates memory, skills, evidence, authority, and verification.
- You are creating a reusable project/profile/SSOT/taskpool flow from research or external examples.

Do not use for:
- Simple one-shot Q&A where live lookup alone suffices.
- Storing task progress in durable memory.
- Treating a vector database or long context window as the whole solution.
- Expanding tool authority merely because more context is available.

## Core Model

Represent context as an assembly function:

```text
Context = Assemble(
  instructions,
  objective,
  constraints,
  knowledge,
  tools,
  authority,
  memory,
  project_state,
  evidence,
  query,
  validation
)
```

A good assembly is judged by:
- relevance: directly supports the current goal;
- freshness: not stale relative to the task;
- authority: can safely justify the action being taken;
- cost: token/noise/privacy/contamination overhead;
- traceability: claims can be mapped back to sources;
- verifiability: outputs can be tested or read back.

## Context Packet Template

For complex work, create this packet before acting:

```text
Objective: <success criteria>
Non-goals: <what not to change or claim>
Hard constraints: <safety, product, precision, authority, privacy>
Source facts: <URLs/files/screenshots/API/logs + freshness>
Selected skills/profiles: <why loaded, what they contribute>
Memory boundary: <user stable / project scoped / session only / do-not-save>
Tool authority: <allowed actions, denied actions, rollback/readback>
Execution plan: <small reversible steps>
Validation plan: <tests/API/UI/log/readback/evidence map>
Negative cases: <what must not happen>
```

## Evidence DAG

Track material claims as:

```text
source_id -> extracted_claim -> decision -> action -> readback -> learning_landing
```

Rules:
- Do not cite a source as proof for a claim it does not actually support.
- Session history is evidence of what was said, not proof of current external state.
- Tool output is evidence only within its scope and time slice.
- Screenshots prove rendered UI, not backend semantics, unless paired with API/log readback.

## Landing-Zone Rules

When the run produces reusable learning, choose one landing zone:

| Claim type | Landing zone |
|---|---|
| Stable user preference/red line | user memory |
| Stable project fact | project profile / project SSOT |
| Reusable procedure/checklist | skill |
| Design/architecture decision | ADR / SSOT doc |
| Task proof or one-off artifact | taskpool evidence / session transcript |
| Unverified research signal | evidence brief / experience proposal |
| Unsafe or over-broad rule | do-not-save boundary |

## Common Patterns

### AI Coding Context Packet
- repo profile + AGENTS.md/CLAUDE.md
- relevant source files and similar implementations
- API contracts and data model constraints
- tests/lint/build commands
- UI/API readback requirements
- red lines: no feature loss, no precision downgrade, no state-machine rewrite without evidence

### Agent Runtime Context Packet
- objective and mission state
- skills and tool availability
- side-effect policy and AuthorityGrant
- receipts/readback commands
- memory/project profile boundaries
- failure/retry/rollback plan

### Research-to-Implementation Context Packet
- source list with direct quotes/abstract claims
- taxonomy of transferable mechanisms vs rejected hype
- candidate landing surfaces
- smallest reversible slice
- verification and falsifier

## Common Pitfalls

1. **RAG reductionism** — treating Context Engineering as only vector search. Retrieval is one component; memory, tools, authority, state, and verification are equally important.
2. **Long-context fallacy** — assuming a larger window means the model will use the right facts. Use selection, ranking, positioning, compression, and readback.
3. **Memory ghosting** — saving WIP status, stale decisions, or task artifacts into durable memory. Route them to evidence/SSOT/taskpool instead.
4. **Authority confusion** — more context does not grant permission. Tool execution, external dispatch, deploy, payment, credentials, and destructive actions still need exact authority and readback.
5. **Source laundering** — summarizing a source and later treating the summary as proof. Keep source IDs and claim-level mappings.
6. **Context pollution** — injecting all known preferences, old profiles, or unrelated skills because they are available. Minimal sufficient context beats maximal context.
7. **Plan-as-proof** — a Context Packet is not completion. Completion requires real tests, UI/API/log readback, or explicit boundary stop.

## References

- `references/core-works-and-landing.md` — core Context Engineering works, transferable claims, Hermes landing map, and authority boundaries.
- `references/full-landing-ladder.md` — full safe landing ladder for approved Context Engineering evolution: canon → skill → SSOT/profile → packet contract → deterministic eval → converge matrix → scoped commit → runtime boundary analysis.

## Verification Checklist

- [ ] Objective, non-goals, hard constraints, and negative cases are explicit.
- [ ] Sources are current enough and scoped to the task.
- [ ] Selected memories/skills/project facts are relevant and not stale ghosts.
- [ ] Tool authority is separated from tool knowledge.
- [ ] Evidence DAG maps material claims to source/readback.
- [ ] Execution is broken into reversible slices.
- [ ] Final claims cite real test/API/UI/log/file evidence or state the remaining boundary.
- [ ] Durable learning, if any, is landed in the correct zone rather than dumped into memory.
