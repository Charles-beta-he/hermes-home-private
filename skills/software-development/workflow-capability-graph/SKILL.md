---
name: workflow-capability-graph
description: "Use when absorbing, designing, auditing, or upgrading workflows into composable capability graphs: intent router, input/source model, modules/workflows/agents/gates, tool-pool references, evidence ledgers, closure states, and atomic module checks."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [workflow, capability-graph, agents, modules, gates, abstraction]
    related_skills: [workflow-ecosystem-audit, abstraction-governance, agent-skill-design-patterns, product-workflow-operating-system]
---

# Workflow Capability Graph

## Overview

Use this skill to turn a workflow idea, video/demo, existing process, product pipeline, or agent architecture into a composable capability graph.

Core rule:

```text
Workflow families are capability graphs. Atomic modules, composite modules, workflows, agents, gates, adapters, templates, and tool references are all CapabilityNodes. A node may be a workflow internally and a module externally.
```

Scope: reusable workflow/module/agent architecture design and audit across domains.

Applicability: use for class-level workflow absorption, architecture specs, module library audits, agent wrapper contracts, tool-pool references, and abstraction coverage checks.

Anti-conditions: do not use this skill to store task progress, one-off project facts, local artifact paths as global truth, or to claim runtime implementation coverage from architecture/spec documents alone.

## When to Use

Use when the user asks to:

- “提升/吸收/抽象/覆盖” a workflow, video, repo, product pattern, or agent loop.
- Check whether a workflow is modular enough or has hidden monoliths.
- Split modules to atomic level.
- Define or audit Agent wrappers, tool pools, evidence ledgers, and closure states.
- Compare coverage across workflow families.
- Promote a one-off workflow analysis into a reusable architecture/spec layer.

Don't use for:

- Executing an already well-specified single-step task.
- Saving task progress or one-off artifacts to durable memory.
- Claiming runtime/product implementation coverage from architecture docs alone.

## Core Model

### CapabilityNode

Every reusable unit should declare:

```yaml
id: string
kind: atomic_module | composite_module | workflow | agent_role | gate | adapter | artifact_template
responsibility: string
consumes: []
produces: []
preconditions: []
depends_on: []
subnodes: []
gates: []
agent_wrappers: []
side_effects: none | local_write | external_read | external_write | physical_action | payment | publish | destructive
closure_states: []
can_be_used_as_module: true
can_be_used_as_workflow: true
can_be_delegated_to_agent: true
cannot_prove: []
```

### AgentWrapper

Agents are wrappers around capability nodes, not labels:

```yaml
id: string
wraps: []
role: router | creator | reviewer | orchestrator | executor | monitor | verifier | publisher
policy: []
authority: read_only | local_write | external_read | external_write_requires_gate | physical_action_requires_gate | publish_requires_gate
produces: []
cannot_do: []
```

### Gate

A gate is only real if it has outcomes:

```yaml
outcomes:
  pass: continue
  warn: continue_with_warning
  fail: retry_or_stop
  blocked: human_gate
```

## Procedure

1. **Route by intent**
   - Identify the user's requested deliverable/effect.
   - Separate partial requests from full-chain requests.

2. **Model inputs/sources/assets**
   - Assign roles, quality, authority, freshness, rights, and claim/source boundaries.

3. **Build the capability graph**
   - List atomic modules.
   - Expose composite modules as internal workflows with subnodes.
   - Allow workflows to compose other workflows.

4. **Attach Agent wrappers**
   - For each Agent, define `wraps`, `policy`, `authority`, `produces`, and `cannot_do`.

5. **Attach gates and evidence**
   - Define pass/warn/fail/blocked.
   - Define evidence ledger refs for claims and transitions.

6. **Check atomicity**
   - Atomic modules have one responsibility and stable I/O.
   - Composite modules/workflows must expose subnodes and closure states.

7. **Reference tool pool**
   - Use abstract tool capability IDs before binding concrete tools/providers.
   - Gate external writes, provider uploads, publishing, payment, physical actions, and destructive operations.

8. **Validate**
   - Use schema checks, graph validators, or equivalent read-back to prove coverage and atomicity before claiming completion.

## Reference Patterns

- `references/audio-reactive-animation-absorption.md` — use when absorbing sound-reactive visual demos, waveform/particle/VJ effects, or V1→V2 animation upgrades into capability graphs and runnable prototype slices.
- `references/3d-ip-extension-pack-absorption.md` — use when absorbing public media/design demos or client requests about 2D-to-3D IP/mascot conversion, 3D brand character extension, ecommerce visual packs, social/H5 asset packs, or “老板要看3D的IP延展和套图” workflows.
- `references/superagent-research-harness-absorption.md` — use when absorbing public media/open-source leads about deep-research agents, superagent harnesses, evidence-search workflows, multi-agent report generators, or skill/tool marketplaces into an evidence-backed research-task graph and safe owned prototype slices.
- `references/superagent-research-harness-absorption.md` — use when absorbing public-media/repo leads about deep-research agents, superagent harnesses, evidence-search workflows, subagent report generators, or skill/tool marketplaces into a verified research-task graph with evidence ledger, citation gate, and explicit authority boundaries.
- `references/capability-granular-model-routing.md` — use when upgrading coarse T0/T1/T2/T3 model routing into capability-surface routing: specialist primary model first (Gemini for visual/UI, Claude for review/architecture, GPT/Codex for implementation, MiMo for triage), then risk-layer reviewers/arbiters/evidence gates.
- `references/stable-core-outer-tool-adapters.md` — scope: class-level architecture pattern; applicability: workflow/agent cores expanding into multiple UI, sensory, hardware, storage/archive, or network entrypoints; anti-condition: do not treat architecture coverage as runtime implementation or side-effect authority.
- `references/evidence-gated-agent-lifecycle.md` — use when turning domain agents into lifecycle-governed systems with state schemas, evidence contracts, static/dynamic gate templates, multi-role certification, runtime projection, observability, ratchet, and retirement boundaries.
- `references/evidence-gated-agent-lifecycle.md` — use when a workflow is becoming an agent-generation/runtime system: state model + capability graph + evidence contract + dynamic gates + certification + runtime UX + observability + ratchet/retirement. Includes `DynamicGateManifest` and certification rules.
- `references/embodied-workflow-platform-projectization.md` — use when projectizing a long-term outer-tool/body layer around an assistant core: stable workflow contracts, adapters for multiple entry/device surfaces, evidence/literature pack, portfolio integration, and phased no-hardware-first roadmap.
- `references/raven-everos-agent-harness-absorption.md` — use when absorbing public-media/open-source leads about agent harnesses, self-improving agents, local-first memory runtimes, digital workers, agent templates, proactive/sentinel nudges, or edge/local executor frameworks into Hermes/AgentOS-style capability graphs. Requires source evidence → local SSOT → capability graph → proposal atoms before any runtime/install/skill import.

- `references/agent-template-profile.md` — use when converting Agent Templates, digital workers, Mission templates, or reusable role agents into governed Hermes/AgentOS profiles with source refs, capability graph refs, authority matrix, side-effect matrix, gates, rollback, receipts, and readback.
- `references/reference-repo-absorption-loop.md` — use when absorbing external/public-media/open-source agent or workflow repos into Hermes: pin source identity, build a claim map, generate capability graph nodes, apply Memory Ownership Gate, create proposal atoms, and continue to the next safe local artifact instead of stopping at a report.

## Public-media project absorption execution pattern

When the user authorizes project-level or “全盘推进” absorption of a public video/repo project, do not stop at a report or capability graph if a safe owned prototype slice is available. After preview/artifact verification, land the smallest reversible local implementation that proves the transferable workflow boundary, for example:

```text
source inputs -> source cards -> claim map -> citation gate -> evidence-ledger.json -> report.md
```

Keep third-party runtime installation, imported external skills, credentials, live model/search calls, app-gated content extraction, publishing, and external writes closed unless separately authorized. The completion claim should distinguish: (1) verified public/media/repo facts, (2) local owned prototype proof, and (3) still-unproven upstream/runtime claims.

## Common Pitfalls

1. **Module/workflow false dichotomy** — a big module can be a workflow internally; a workflow can be a module externally.
2. **Agent-as-name trap** — an Agent without wrapped capabilities, policy, authority, and output contract is only a label.
3. **Hidden composite trap** — if a module has many steps but no subnode list, expose its internal workflow.
4. **Gate-as-advice trap** — if a gate has no pass/warn/fail/blocked semantics, it cannot govern execution.
5. **Runtime overclaim** — architecture/spec coverage does not prove provider integration, UI automation, or side-effect execution.
6. **Tool hardwiring** — workflow specs should reference tool capability classes first, then bind concrete tools by availability, authority, and cost.

## Verification Checklist

- [ ] The requested workflow family has an intent router with partial and full-chain routes.
- [ ] Inputs/sources/assets are role-modeled with authority and quality boundaries.
- [ ] Capability nodes have stable consumes/produces.
- [ ] Composite modules expose internal subnodes.
- [ ] Workflows can be reused as modules when they have stable I/O and closure states.
- [ ] Agent wrappers define `wraps`, `policy`, `authority`, `produces`, and `cannot_do`.
- [ ] Gates define pass/warn/fail/blocked outcomes.
- [ ] Evidence ledger can support claims and stage transitions.
- [ ] Side effects and human gates are explicit.
- [ ] Atomicity validator or equivalent audit passed before claiming 100% spec coverage.
