---
name: abstraction-governance
description: Use when turning incidents, project experience, user corrections, or agent self-critiques into the right abstraction layer without coupling local context to global rules.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [abstraction, governance, experience, memory, skills, metacognition]
    related_skills: [agent-boundary-audit, hermes-experience-ratchet, qian-meta-synthesis, documentation-and-adrs, hermes-agent-skill-authoring, skill-eval]
---

# Abstraction Governance

## Overview

Use this skill to govern the path from a concrete event to a reusable rule. The goal is not to "abstract more"; the goal is to choose the correct abstraction layer, strip local entities before generalization, preserve source/evidence boundaries, and land each claim in the right Hermes surface.

This skill is especially important after a project incident, Git workflow failure, user correction, multi-model review, or any discussion about Agent norms. It prevents two failure modes:

- under-abstraction: keeping only a local story that cannot transfer;
- over-abstraction/context coupling: turning local facts into global rules or producing a principle too vague to execute.

## When to Use

- A concrete incident, project lesson, or user correction may become future guidance.
- The user asks where to store a lesson: memory, project profile, skill, gate, ADR, or taskpool.
- A prior answer was too context-coupled, too generic, or tied to a specific example.
- You need to decide whether a lesson should become a pattern, procedure, runtime gate, ADR, or meta-policy.
- Multi-model or research output produced methodology rather than only a one-off answer.

Don't use for:

- Simple factual answers with no durable learning implication.
- Active task progress, PR numbers, issue numbers, or temporary TODOs.
- A project fact that can be read from the repo/profile and does not need abstraction.

## Core Principle

Before generalizing, separate:

1. event facts — what happened;
2. local context — what is only true here;
3. entity names — paths, branch names, repo names, ports, commands, one-off artifacts;
4. transferable structure — roles, relations, failure mechanism, constraints;
5. executable rule — what an agent can check or do next time;
6. governance landing zone — where the rule belongs.

A valid abstraction must answer: scope, source, applicability, anti-conditions, falsifier, storage target, and operationalization.

## Abstraction Ladder

| Level | Name | Stores | Example |
|---|---|---|---|
| L0 | Event / trace | session log, Workpad, incident log | "A branch merge went wrong in this repo." |
| L1 | Project fact | project profile, AGENTS.md, Workpad boot | "This repo's integration branch is X." |
| L2 | Scenario pattern | skill reference, experience atom | "Branch names do not equal branch roles in multi-branch projects." |
| L3 | Operational rule | skill checklist/runbook | "Before merge/rebase/push, resolve base/head/upstream/worktree." |
| L4 | Runtime gate | preflight hook, policy, CI, taskpool gate | "Side-effecting Git operations require branch-role preflight." |
| L5 | ADR / decision | docs/adr, project decision log | "This project uses PR-only merges to protected branches." |
| L6 | Meta-policy | agent governance skill/policy | "Local incidents must pass scope tagging and entity stripping before promotion." |
| L7 | Cognitive mechanism | eval/checker/self-audit | "Detect default-schema misuse and context-coupled abstraction." |

Do not skip levels. A single incident can produce multiple claims at different levels, but each claim must be split and landed separately.

## Pipeline

### 1. Frame the problem

Ask internally:

- Is the user asking for content, method, governance, self-correction, or meta-governance?
- What is the desired state?
- What would count as a bad abstraction here?

### 2. Capture event and source boundary

Record only enough to keep provenance:

- source: user statement, tool output, project file, multi-model result, or session trace;
- confidence: verified, inferred, model opinion, or user correction;
- evidence refs: file paths, commands, transcript references, or cited works.

Multi-model agreement is not truth. It is expert signal until grounded by evidence or falsifier review.

### 3. Scope-tag every candidate claim

Allowed scopes:

- task — current task only;
- session — current conversation only;
- project — one named project;
- repo — one repository;
- domain — a family of projects/tasks;
- user — stable user preference/red line;
- global — all agent behavior.

No scope, no promotion.

### 4. Strip entities before generalization

Remove or parameterize:

- project names;
- branch names;
- file paths;
- user-local ports;
- one-off commands;
- temporary workarounds;
- specific model names unless the rule is about model routing.

Then ask: what relationship remains?

Bad: "Do not treat feat/uvisa-2.0 as head."
Good: "Do not infer branch role from branch name; resolve base/head/integration/release roles from project context before side-effecting Git operations."

### 5. Extract the pattern

Use this form:

```text
Context: <where this pattern appears>
Problem: <failure mechanism>
Forces: <competing needs/constraints>
Solution: <structural rule>
Consequences: <costs and benefits>
Anti-conditions: <when not to apply>
Falsifier: <what would disprove or narrow it>
```

### 6. Choose the landing zone

| Claim shape | Landing zone |
|---|---|
| one-off trace or recovery detail | session log / Workpad / incident log |
| stable project-specific fact | project profile / repo docs |
| stable user preference or red line | memory, compact declarative form |
| reusable procedure | skill |
| mandatory safety mediation | runtime gate / hook / policy / CI |
| team/project governance decision and rationale | ADR |
| candidate cross-project lesson needing review | experience-ratchet atom/proposal |
| concrete future engineering work | taskpool candidate |
| unsafe authority expansion | do-not-do boundary |

### 7. Evidence gate

Promote only when one of these is true:

- repeated across contexts;
- single event but high severity/systemic risk;
- explicitly confirmed by the user as durable preference/red line;
- supported by project docs or tool evidence;
- grounded by literature and converted to an executable falsifier.

Do not promote when:

- the claim is only a model opinion;
- the claim still contains local entities;
- it lacks anti-conditions;
- it cannot be operationalized;
- it would over-constrain unrelated tasks.

### 8. Operationalize

A useful abstraction should become at least one of:

- checklist;
- preflight;
- script;
- hook;
- CI check;
- ADR template;
- project-profile field;
- skill trigger/counter-trigger;
- eval case;
- taskpool policy.

If it cannot be operationalized, keep it as an explanatory note or experience atom until it matures.

## First-Principles Operationalization

Use "first principles" as an executable decision discipline, not as a slogan that blocks ordinary progress.

Good operational form:
- Start from goal function, canonical facts, constraints, permission boundaries, and verifiable outcome.
- Do not blindly follow templates, prior habits, or tool preferences; however, do reuse proven skills/checklists when they still fit the goal and constraints.
- Ask for clarification only when the ambiguity would change execution path, side effects, authority, acceptance criteria, or long-term architecture. Otherwise act on the safest reversible default.
- If the user's requested path is not the best route to the stated goal, say so and offer the lower-cost / safer / more verifiable path without unnecessarily blocking a clearly authorized request.
- For failures, reproduce and identify root cause before patching symptoms; each key decision should be able to answer why this path, why this evidence source, and how completion will be verified.
- Compress output to information that changes the user's decision, execution path, or risk assessment.

Anti-patterns:
- Turning "first principles" into generic philosophical preamble.
- Asking the user to restate obvious defaults.
- Treating "do not start from templates" as "ignore skills"; skills are experience compression, not a substitute for checking fit.
- Promoting a creator/social-media claim directly into global agent rules without scope, anti-conditions, and falsifiers.

## Agent Psychology Checks

Run these checks for abstraction-heavy work:

1. Frame check — what interpretation frame did I choose, and is there a better one?
2. Level check — which L0-L7 level is the current claim on?
3. Schema check — what default script am I applying; which slots are facts vs guesses?
4. Transfer check — source context, target context, shared structure, differences, non-transferable parts.
5. Structure-mapping check — am I mapping entities or relationships?
6. Counterexample check — when would this rule be wrong?
7. Evidence check — user statement, tool output, project doc, multi-model signal, or external source?
8. Control check — can this become a guard/check/test, or is it only prose?
9. Decay check — should it expire, be reviewed, or demoted on contradiction?
10. Double-loop check — is this only an action fix, or does it expose a flawed assumption/rule-generation mechanism?

See `references/agent-psychology-core-works.md` for the theory map behind these checks.

## Multi-Model / Research Use

When using multiple models or sources:

- keep source/evidence separate from model interpretation;
- preserve dissent instead of flattening to consensus;
- ask one lane for theory/source boundaries, one for engineering landing zones, and one for critique/context-coupling risks;
- require at least one falsifier for any nontrivial governance claim;
- land model output as an experience-ratchet proposal unless the current session already has direct evidence and authorization to edit a skill/profile/memory.

## Output Template

```text
Abstraction Governance Result
- Frame: <content/method/governance/meta-governance>
- Event/source: <what happened + evidence>
- Local facts: <project/session only>
- Entity-stripped pattern: <transferable structure>
- Level: <L0-L7>
- Scope: <task/session/project/repo/domain/user/global>
- Landing zone: <where it belongs>
- Operationalization: <checklist/gate/script/ADR/eval/etc.>
- Anti-conditions: <when not to apply>
- Falsifier: <what would demote/narrow it>
- Next action: <write/patch/propose/queue/ask-human>
```

## Common Pitfalls

1. Treating a vivid local incident as a global rule without entity stripping.
2. Producing a high-level slogan with no executable gate or storage decision.
3. Saving WIP/session progress to memory instead of a trace or Workpad.
4. Putting project facts in a global skill instead of a project profile.
5. Treating multi-model agreement as evidence instead of expert signal.
6. Skipping anti-conditions, which makes the abstraction impossible to demote safely.
7. Confusing action repair with double-loop learning; sometimes the rule-generation process is the bug.
8. Letting a default task schema fill missing slots without marking them as assumptions.

## Memory Landing-Zone Classifier

Scope: global Hermes abstraction/memory governance. Applicability: use before writing durable memory, user profile facts, project profiles, skills, ADRs, or experience-ratchet notes. Anti-conditions: do not use this section to preserve task progress, secrets, local-only project facts, or social-media claims without independent evidence.

For any candidate durable memory, choose the smallest sufficient authority boundary before writing:

```text
0. Secret/credential/payment/private key? -> DO NOT SAVE; redact as [REDACTED] in evidence.
1. Current turn/session only? -> active context / compaction only.
2. Task progress, WIP status, PR/issue/commit, phase done, transient plan? -> taskpool proof / session transcript; not global memory.
3. Stable user preference or red line likely true across 10+ sessions? -> compact declarative user memory.
4. Stable project/environment fact scoped to one project? -> project profile / scoped evidence doc.
5. Reusable procedure, workflow, checklist, or debugging approach? -> skill / skill patch.
6. Event-specific experience or prior conversation recall? -> session_search / proof artifacts; promote only class-level lessons.
7. Entity knowledge? -> structured project profile unless it is truly cross-project stable.
8. Large semantic corpus? -> explicit RAG/vector project only with provenance, deletion, privacy, cost, and drift gates.
```

Map source memory classes to Hermes surfaces:

- short-term memory -> active context and compaction summary;
- long-term memory -> memory / user profile only for stable compact facts;
- entity memory -> project profiles, scoped profiles, or structured docs;
- episodic/contextual memory -> session_search, taskpool evidence, and proof artifacts.

Before any durable write, run the anti-ghost save gate:

1. Will this still be true in 10 sessions?
2. Is it declarative rather than imperative?
3. Is it free of task progress and artifact IDs likely stale in 7 days?
4. Is the scope correct: user/global vs project vs session vs task?
5. Is there a removal/replacement path if it becomes false?
6. Did the user explicitly correct a preference, or is this inferred from one event?
7. Would saving it cause future sessions to repeat old work or override current instructions?

Use preference-drift checks when newer user behavior or scoped project facts contradict old memory: keep, scope_down, ask_confirm, replace, or remove. Do not install or trust third-party memory servers merely because they claim high recall; treat them as design references until privacy, encryption, concurrency, tests, and deletion semantics are verified.

## Sanitized Experience Pack Boundary

When converting a mature personal/local Hermes setup into an installable distribution for other users, package the *capability shape*, not the owner's lived state. Safe landing zones are templates, checklists, example schemas, and deterministic selfchecks; forbidden payloads include live config, `.env`, tokens, OAuth sessions, memory/session DBs, real project profiles, logs, task evidence, and local brain vaults. Installer extensions should copy missing template files without overwriting user edits and expose an opt-out such as `--skip-experience-pack`. See `references/sanitized-experience-pack-boundary.md`.

## Runtime Gate Implementation

Hermes core now includes a deterministic hot-path memory gate in `agent/abstraction_governance.py`, wired through `tools/memory_tool.py`.

Default behavior:

- enabled unless `HERMES_ABSTRACTION_GOVERNANCE_GATE=0`;
- routes deterministic durable-write review through `review_durable_write(kind=..., target=..., content=...)`;
- memory writes: blocks high-confidence task/session progress, and redirects procedure/checklist/workflow content from always-on `memory` to skill or experience-ratchet landing zones;
- skill mutations: allows reusable procedures, but blocks task/session progress and project-specific entities that lack explicit scope/applicability/anti-condition markers;
- allows compact declarative user preferences and scoped project facts;
- returns a structured `abstraction_governance` payload naming reason, recommended landing zone, and required skill.

Current hot-path wiring:

- `tools/memory_tool.py` for `memory(action=add|replace)`;
- `tools/skill_manager_tool.py` for `skill_manage(action=create|edit|patch|write_file)`;
- `tools/file_tools.py` for `write_file` / `patch` when the path targets narrow Hermes governance surfaces;
- `model_tools.handle_function_call()` for common external MCP filesystem mutations (`mcp_filesystem_write_file`, `mcp_filesystem_edit_file`, `mcp_filesystem_move_file`) before generic registry dispatch, so MCP writes cannot bypass the same gate.

Governed filesystem surfaces:

- `~/.hermes/project-profiles/*.{json,yaml,yml}` → `project_profile`;
- `~/.hermes/docs/adr/**` or `~/.hermes/docs/adrs/**` → `adr`;
- `~/.hermes/experience-ratchet/**` → `experience`.

Move/rename operations into governed surfaces are blocked when content is opaque; read the source and rewrite through a reviewed `write_file` / `patch` path instead.

The runtime gate is intentionally deterministic and conservative. It is not a substitute for full abstraction review; it catches obvious boundary violations before they enter persistent prompt context. Ordinary project file writes are not classified by this gate; they continue through normal file/write guards.

## Verification Checklist

- [ ] The claim is split into event, local fact, pattern, rule, gate, ADR, or meta-policy pieces.
- [ ] Every durable claim has scope, source, applicability, anti-condition, and falsifier.
- [ ] Local entities were stripped or explicitly kept in a project-scoped landing zone.
- [ ] Storage target was chosen before writing memory/skill/profile/ADR/taskpool.
- [ ] Any skill/profile/memory change was read back after writing.
- [ ] Any runtime/code gate is proposed or implemented with verification, not merely described.
- [ ] Dissent and uncertainty are preserved for multi-model/research-derived claims.
- [ ] The final report says what was landed, what was only proposed, and what requires human approval.
