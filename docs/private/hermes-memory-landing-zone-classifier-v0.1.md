# Hermes Memory Landing Zone Classifier v0.1

Generated: 2026-06-14
Task: `2026-06-14-agent-memory-选型决策树吸收记忆落点分类与反幽灵门禁到-hermes-memory-governance`

## Evidence inputs

- Agent Memory Douyin intake: `/Users/charles/.hermes/docs/private/douyin-agent-memory-system-7650926105133583652/intake-analysis.md`
- NexSandglass Douyin intake: `/Users/charles/.hermes/docs/private/douyin-nexsandglass-7648988722738249445/intake-analysis.md`

## Goal

Route every potential memory item to the smallest sufficient durable boundary, while preventing stale ghosts, WIP/status leakage, and secret persistence.

Core rule:

```text
Memory is not “save more”. Memory is “put the right fact in the right authority boundary with provenance, expiry, and removal semantics”.
```

## Landing-zone decision tree

```text
0. Does the content include secrets, credentials, tokens, passwords, private keys, connection strings, or payment data?
   → DO NOT SAVE. Redact as [REDACTED] if evidence must mention existence.

1. Is it needed only for the current turn/session?
   → Active conversation context only.
   → Do not write durable memory.

2. Is it task progress, WIP status, a PR/issue/commit number, “phase done”, “submitted”, “fixed bug”, or a transient plan?
   → Taskpool note / proof artifact / session transcript.
   → Do not write memory.

3. Is it a stable user preference likely true across 10+ sessions?
   → `memory(target="user")` after confidence check.
   → Examples: language preference, communication style, stable red lines.

4. Is it a stable environment/project fact scoped to one project?
   → Project profile or project-scoped evidence doc.
   → Do not put local project facts into global user memory.

5. Is it a reusable procedure, workflow, debugging pattern, or repeated successful approach?
   → Skill candidate / skill patch.
   → Procedures belong in skills, not memory.

6. Is it an event-specific experience, prior conversation, debug trail, or “where did we leave X” material?
   → `session_search`, taskpool evidence, proof artifacts.
   → Do not summarize into global memory unless it has become stable policy.

7. Is it entity knowledge such as people, repos, services, channels, app URLs, branch policies, or integration boundaries?
   → Structured project profile when scoped; user profile only when it is a stable user/entity fact.

8. Is it a large corpus or semantic knowledge base need?
   → RAG/vector candidate only after provenance, deletion, cost, privacy, and drift gates.
```

## Mapping from source memory taxonomy to Hermes authority boundaries

- Short-term memory
  - Source definition: single-session context messages.
  - Hermes landing zone: active context + compaction summary.
  - Save rule: no durable write unless another gate below qualifies.

- Long-term memory
  - Source definition: cross-session durable preference/experience.
  - Hermes landing zone: `memory` / `user profile` only for stable, compact declarative facts.
  - Save rule: no WIP, no stale progress, no secrets, no temporary intent.

- Entity memory
  - Source definition: names, projects, teams, objects.
  - Hermes landing zone: project profile / scoped profile / structured docs; only global memory if cross-project stable.
  - Save rule: include source/provenance and scope.

- Episodic / contextual memory
  - Source definition: specific events and past problem-solving episodes.
  - Hermes landing zone: `session_search`, taskpool notes, proof artifacts.
  - Save rule: recall on demand; promote to skill only after repeated class-level value.

## Design pattern selection table

- Sliding window + summary
  - Use for: normal conversation and compaction.
  - Hermes mechanism: context + compacted handoff.
  - Gate: preserve latest objective, constraints, evidence, unresolved blockers.

- Layered memory
  - Use for: production-grade assistant behavior.
  - Hermes layers: active context → session_search → memory/user → project profile → skills → evidence docs/RAG.
  - Gate: do not let lower-authority layers override project SSOT or explicit user correction.

- Tool-driven memory
  - Use for: explicit `remember this`, stable preference corrections, environment facts.
  - Hermes mechanism: `memory` tool / `skill_manage` / profile update.
  - Gate: classify before write; reject WIP, secrets, task progress, and local-only facts.

- Reflection loop
  - Use for: post-task experience ratchet after complex tasks.
  - Hermes mechanism: propose/patch skill, not blanket memory.
  - Gate: repeated class-level lesson, readback proof, no stale session state.

## Anti-ghost save gate

Before any durable write, answer:

1. Will this still be true in 10 sessions?
2. Is it declarative rather than imperative?
3. Is it free of task progress and artifact IDs likely stale in 7 days?
4. Is the scope correct: user/global vs project vs session vs task?
5. Is there a removal/replacement path if it becomes false?
6. Did the user explicitly correct a preference, or is this inferred from one event?
7. Would saving it cause future sessions to repeat old work or override current instructions?

If any answer is unsafe, do not save to global memory.

## Preference drift / stale-memory check

Use NexSandglass’ “偏移率检测” idea as policy, not as an unverified MCP install.

A memory item becomes `drift_suspect` when:

- the user explicitly contradicts it;
- 2+ recent sessions show behavior or instructions inconsistent with it;
- a project profile supersedes it with newer scoped facts;
- the old memory contains a time-sensitive convention or tool behavior;
- the memory is broad but current request is clearly scoped differently.

Actions:

```text
keep        — no conflict, still stable
scope_down  — move interpretation to project/session scope
ask_confirm — user preference conflict materially affects action
replace     — explicit user correction or stable repeated evidence
remove      — false/stale/harmful entry
```

## RAG/vector escalation gate

Only escalate beyond FTS/session_search/project docs when all are true:

- corpus size or query semantics exceed simple retrieval;
- provenance and deletion semantics are defined;
- embedding/model drift is considered;
- private data boundary is approved;
- cost/latency budget is explicit;
- retrieval output is treated as context, not authority;
- project SSOT remains higher authority than vector hits.

## Runtime checklist for Hermes answers

When user says “remember”, “吸收”, “沉淀”, or a task yields a lesson:

1. Classify landing zone.
2. If memory: write compact declarative fact only.
3. If procedure: patch/create skill after user approval where required.
4. If project fact: update project profile/evidence, not global memory.
5. If event: rely on session_search/taskpool evidence.
6. If uncertain: state the uncertainty and avoid durable write.

## Non-goals

- This artifact does not implement a new memory backend.
- This artifact does not install NexSandglass or any MCP server.
- This artifact does not replace Hermes memory/session_search/skills.
- This artifact does not authorize storing raw private conversations in plaintext or vector DB.

## Verification mapping

Acceptance item coverage:

- memory landing-zone decision tree: covered in `Landing-zone decision tree`.
- four memory classes mapping: covered in `Mapping from source memory taxonomy`.
- design pattern selection: covered in `Design pattern selection table`.
- anti-ghost save gate: covered in `Anti-ghost save gate`.
- RAG/vector escalation gate: covered in `RAG/vector escalation gate`.
- NexSandglass preference-drift insight: covered in `Preference drift / stale-memory check`.
