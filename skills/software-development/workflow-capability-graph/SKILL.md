---
name: workflow-capability-graph
description: "Use when absorbing, designing, auditing, or upgrading workflows into composable capability graphs: intent router, input/source model, modules/workflows/agents/gates, tool-pool references, evidence ledgers, closure states, and atomic module checks."
version: 1.2.3
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
- Choose the narrowest Hermes landing seam when cron providers, cron payloads, plugin CLI, Missions, workflow-kernel helpers, delegation, and taskpool appear to overlap.
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

- `references/hermes-existing-orchestration-seam-landing.md` — use when choosing the smallest safe Hermes integration across plugin CLI, cron jobs/providers, Missions, workflow-kernel helpers, delegate, and Kanban/taskpool. Distinguishes timer backend from payload executor and task ownership; requires structural default-off/local-only behavior plus positive and negative evidence.
- `references/agent-runtime-personalization-forensics.md` — use when reconstructing or comparing coding-agent/CLI-assistant work logic from global/project instructions, hooks, skills, plugins, permissions, SQLite state, and session journals. Enforces read-only evidence collection, privacy-safe aggregation, `installed → enabled → manifest-declared → registered → observed` activation grading, WAL-aware SQLite reads, immutable snapshot provenance/manifest, report-to-evidence drift checks, deterministic bundle verification, and independent-verifier certification boundaries.
- `references/layered-project-card-runtime-overlay.md` — use when organizing a multi-project agent platform as a shared consensus base plus switchable project overlays. Defines the layers × planes × capability-graph model, ProjectCard contract, profile/workspace/sandbox boundary, project-switch decontamination gate, and upstream/local/runtime/project truth separation.
- `references/compound-engineering-modular-absorption.md` — use when absorbing Every/AI MBA Compound Engineering / 复利工程 / Plan→Work→Review→Compound into Hermes, taskpool, project workflows, or skill systems as a capability graph with prior-context intake, objective plan, vertical work slice, evidence packet, review matrix, compound writeback router, and next-loop hook. Template: `templates/compound-engineering-loop.yaml.md`.
- `references/audio-reactive-animation-absorption.md` — use when absorbing sound-reactive visual demos, waveform/particle/VJ effects, or V1→V2 animation upgrades into capability graphs and runnable prototype slices.
- `references/3d-ip-extension-pack-absorption.md` — use when absorbing public media/design demos or client requests about 2D-to-3D IP/mascot conversion, 3D brand character extension, ecommerce visual packs, social/H5 asset packs, or “老板要看3D的IP延展和套图” workflows.
- `references/superagent-research-harness-absorption.md` — use when absorbing public media/open-source leads about deep-research agents, superagent harnesses, evidence-search workflows, multi-agent report generators, or skill/tool marketplaces into an evidence-backed research-task graph and safe owned prototype slices.
- `references/superagent-research-harness-absorption.md` — use when absorbing public-media/repo leads about deep-research agents, superagent harnesses, evidence-search workflows, subagent report generators, or skill/tool marketplaces into a verified research-task graph with evidence ledger, citation gate, and explicit authority boundaries.
- `references/capability-granular-model-routing.md` — use when upgrading coarse T0/T1/T2/T3 model routing into capability-surface routing: specialist primary model first (Gemini for visual/UI, Claude for review/architecture, GPT/Codex for implementation, MiMo for triage), then risk-layer reviewers/arbiters/evidence gates.
- `references/stable-core-outer-tool-adapters.md` — scope: class-level architecture pattern; applicability: workflow/agent cores expanding into multiple UI, sensory, hardware, storage/archive, or network entrypoints; anti-condition: do not treat architecture coverage as runtime implementation or side-effect authority.
- `references/evidence-gated-agent-lifecycle.md` — use when turning domain agents into lifecycle-governed systems with state schemas, evidence contracts, static/dynamic gate templates, multi-role certification, runtime projection, observability, ratchet, and retirement boundaries.
- `references/evidence-gated-agent-lifecycle.md` — use when a workflow is becoming an agent-generation/runtime system: state model + capability graph + evidence contract + dynamic gates + certification + runtime UX + observability + ratchet/retirement. Includes `DynamicGateManifest` and certification rules.
- `references/external-jspace-workspace-projection.md` — use when absorbing interpretability or “model internal state” ideas such as Anthropic J-space / Global Workspace into Hermes/AgentOS/taskpool workflows as an external, auditable workspace projection: WorkspaceProjection + EvidenceDAG + ReflectionReadback + AuthorityGate + SurfaceModelReview + CompletionClaimGate. For local packet shape, use `templates/workspace-projection-packet.sample.json` and validate with `/Users/charles/.hermes/scripts/workspace_projection_gate.py`. Anti-condition: never claim closed-model hidden-state access or allow model votes to close completion-critical claims without objective evidence.
- `references/anthropic-global-workspace-external-projection.md` — condensed primary-source absorption and reusable gate checklist for Anthropic Global Workspace / J-space research: source facts to preserve, engineering translation, validator fail-closed cases, and the dashboard-history pitfall where aggregate prior runtime/taskpool flags must not be mistaken for current-task authorization.
- `references/embodied-workflow-platform-projectization.md` — use when projectizing a long-term outer-tool/body layer around an assistant core: stable workflow contracts, adapters for multiple entry/device surfaces, evidence/literature pack, portfolio integration, and phased no-hardware-first roadmap.
- `references/reference-repo-absorption-loop.md` — use when absorbing public-media/open-source leads about agent harnesses, self-improving agents, local-first memory runtimes, digital workers, agent templates, proactive/sentinel nudges, edge/local executor frameworks, or other external agent/workflow repos into Hermes/AgentOS-style capability graphs. Requires source evidence → local SSOT → capability graph → proposal atoms before any runtime/install/skill import.
- `references/evidence-calibrated-course-absorption.md` — use when turning a multi-record course or lecture corpus into durable capabilities: prove source identity (including SPA stale-state risks), build a typed claim ledger, calibrate facts and numbers, reconstruct a capability graph, run counterexample/scenario evals, apply landing-zone ownership, and ratchet only independently evidenced procedures.
- `references/external-search-adapters-in-execution-graphs.md` — use when adding broad-web, documentation, repository, social, or page-fetch providers to a governed execution graph: model each as a bounded external-read adapter, run the fake-edge/shared-resource check, preserve typed errors and URL provenance, separate search/reduce/verify, and keep credentials, cost, and external-write authority gated.
- `references/external-system-prompt-absorption.md` — use when a public repository claims to contain a leaked/distilled/universal system prompt. Pin identity, separate prompt-text facts from provenance/equivalence marketing claims, classify each rule as accept/conditional/reject, keep activation and authority closed, and require state/evaluator/evidence/budget/termination contracts before calling prompt prose an agent architecture.

- `references/agent-template-profile.md` — use when converting Agent Templates, digital workers, Mission templates, or reusable role agents into governed Hermes/AgentOS profiles with source refs, capability graph refs, authority matrix, side-effect matrix, gates, rollback, receipts, and readback.
- `references/agent-cli-startup-handshake.md` — use when designing terminal-native Agent startup UX as a read-only readiness handshake: fast local probes, banner/statusline/mode-badge projection, explicit repair slash commands, and no automatic LLM/API/session-history mutation.
- `references/reference-repo-absorption-loop.md` — use when absorbing external/public-media/open-source agent or workflow repos into Hermes: pin source identity, build a claim map, generate capability graph nodes, apply Memory Ownership Gate, create proposal atoms, and continue to the next safe local artifact instead of stopping at a report.
- `references/ai-coding-workbench-audit.md` — use when evaluating or absorbing AI coding desktops, IDE-like agent workbenches, Worktree multi-task systems, model-provider hubs, usage dashboards, or extension marketplaces. Separates IDE/editor claims from agent wrappers, audits worktree isolation versus shared integration locks, distinguishes tool approval from extension-code authority, and defines a staged verification ladder.
- `references/functional-library-module-pool-absorption.md` — scope: class-level multi-feature repository absorption; applicability: repositories containing many runnable features/templates/apps where selected functionality should become reusable capability; anti-condition: skip for a single stable package or summary-only request. Covers deterministic inventory, deduplicated capability families, kernel-vs-domain recommendation, side-effect-free temporary workflows, `local_contract_verified` → bounded `owned_runtime_slice_verified` promotion, immutable RAG evidence packets, owned read-only stdio MCP slices, and classifier-vs-evidence-emitter pre-commit debugging with shared dirty-index preservation.
- `references/evidence-bound-open-source-absorption.md` — use when open-source projects can supply capture/parser/OCR/state/archive workflows but not upstream data or transaction authority. Covers code-license vs data-rights separation, provider-neutral evidence contracts, fail-closed promotion gates, negative tests, source-mode consumer regression checks, and the remaining real-API dossier.
- `references/workflow-asset-loop-engineering.md` — use when a vague/repeated user process may deserve becoming a governed workflow asset. Key rule: do not hard-trigger on “创建工作流”; score reuse value, risk, evidence gap, authority boundary, longevity, output-contract need, routing collision risk, and cleanup cost; then land as no-write/session plan/template fragment/project SSOT/workflow candidate/skill reference/experience-ratchet/taskpool/cron only as warranted.
- `references/absorption-closeout-and-backlog.md` — use at closeout or “what remains?” time: reconcile current state against stale report text, apply safe local proposals instead of stopping at review language, fold reusable lessons into class-level umbrellas, triage remaining work as P0/P1/P2/P3 backlog, and commit exact scoped files only.
- `references/workflow-asset-lifecycle-and-creation-gate.md` — use when deciding whether a fuzzy request, repeated behavior, or user correction should become a governed workflow asset. Key rule: workflow creation is not keyword-triggered; judge by reuse value, risk surface, evidence gap, governability, and long-termity, then land in the right layer with lifecycle, output contract, gates, route eval, model-routing policy, promotion/demotion, and cleanup rules.

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
7. **Attribution drift** — never attribute a rule to a source from memory or a prior summary; require a pinned line/span and correct downstream SSOTs when a full-source pass disproves the attribution.
8. **Manual-summary drift** — derive rule-classification totals and graph coverage from machine-readable records; hand-counted report totals can contradict the underlying matrix.
9. **Unnamed-measurement overclaim** — token counts, compression ratios, and behavioral-equivalence claims need named measurement contracts and available baselines; otherwise report `not reproduced` or `untested`, not universal falsity or equivalence.
10. **Timer/executor/task-owner collapse** — do not treat the component that decides when work fires, the component that executes a payload, and the system that owns task claims/status as one interchangeable scheduler surface. Classify each responsibility before choosing an extension point.
11. **Discovery-as-authority error** — loading or discovering a plugin is not authority to create jobs, threads, state, or external effects; default-off features need a separate explicit enable transition.

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
- [ ] Timer backend, payload executor, and task ownership/claim plane are classified separately before selecting an integration seam.
- [ ] Default-off claims have negative evidence that import/discovery/status do not create jobs, threads, or mutable runtime state.
- [ ] “Local-only” claims distinguish local execution/delivery from stronger OS-level network isolation.
- [ ] For forensic audits, installed/enabled/manifest-declared/registered/observed states are not conflated.
- [ ] Durable evidence excludes raw permission patterns, private command arguments, session bodies, and hidden reasoning.
- [ ] Every source-attributed rule has an exact line/span in the pinned artifact; prior summaries are not treated as source evidence.
- [ ] Quantitative claims name tokenizer/metric/version and include the required baseline, or are explicitly marked `not reproduced`/`untested`.
- [ ] Rule totals and graph-coverage counts are mechanically derived and asserted against machine-readable records.
- [ ] Universal compatibility or behavioral equivalence has an isolated, repeated A/B benchmark with named models and critical-failure criteria—or remains unproven.
- [ ] Atomicity validator or equivalent audit passed before claiming 100% spec coverage.
