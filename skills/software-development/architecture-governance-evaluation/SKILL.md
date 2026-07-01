---
name: architecture-governance-evaluation
description: "Use when evaluating, grounding, or redesigning software architecture: theory audits, external framework/tool assessment, cloud-edge/personal-assistant design, distributed worker patterns, migration value, and prioritized architecture improvement plans."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [architecture, evaluation, theory, cloud-edge, migration, distributed-systems]
    related_skills: [project-evidence-grounding]
---

# Architecture Governance and Evaluation

## Overview

This umbrella covers architecture-level judgment: extracting a system shape, mapping it to principles/theory, comparing it with external frameworks, designing cloud-edge/worker systems, and turning gaps into migration or improvement plans.

## When to Use

- User asks for architecture theory, theoretical foundation, or academic grounding
- User asks to evaluate an external framework/tool/platform for Hermes or another system
- Designing cloud brain / local edge worker / multi-device assistant / distributed task execution
- Refactoring complex architecture while preserving behavior
- Building migration plans from a framework or architecture audit

Don't use for:
- Local bugfixes where the architecture is already settled
- UI implementation details without system-design implications
- Literature review with no architecture decision attached

## Evaluation Pipeline

1. **Extract components and data flow**: modules, services, storage, interfaces, execution boundaries.
2. **Map primitives**: internal primitives, external framework concepts, cloud/edge responsibilities, task lifecycle, memory/state, evidence/proof, and worker boundaries.
3. **Ground in theory**: scheduling, concurrency, state machines, distributed systems, safety, queueing, event sourcing, formal verification, and decision theory where relevant.
4. **Identify gaps**: missing component, weak theory, wrong abstraction, integration risk, security boundary, or migration mismatch.
5. **Prioritize**: immediate operational gaps, short-term verifiability, long-term capability unlocks.
6. **Produce a phased plan**: reversible slices with evidence gates and rollback criteria.

## Subproblem Map

| Subproblem | What to do |
|---|---|
| Theory audit | Map each component to explicit foundations and missing constraints. |
| External framework evaluation | Extract architecture, map to local primitives, score migration value vs difficulty. |
| Open-source capability absorption | Treat external features as candidate capabilities; require evidence verification, rollback/fallback, and maintenance readiness before mainline promotion. See `references/open-source-capability-absorption-governance.md`. |
| Open-source capability absorption | Treat external features as candidate capabilities: decompose problem/capability/interface/implementation/verification, map to local primitives, then land via adapter + registry + policy gate + harness + shadow mode before mainline adoption. |
| Cloud-edge assistant design | Separate brain decision/state from local stateless execution; enforce auth, audit, allowlists, and centralized memory. |
| Canonical projection/mobile companion pipelines | Keep the brain/source DB authoritative, make mobile/PWA/local model read-only over projection caches, and require staging/merge/promotion gates before serving enriched cache. See `references/canonical-projection-pipeline-stability.md`. |
| Architecture refactoring | Classify core/deprecated/integrated components, migrate essential features, then validate. |
| Distributed worker/task systems | Preserve a single task-pool SSOT; workers are execution-only unless a deliberate control-plane design says otherwise. |

## Open-source Capability Absorption

When the goal is to implement and strengthen selected features from open-source projects inside the user's own architecture, do not start by copying code into core. Run a governed capability-intake path:

1. Decompose the source feature into problem, capability, interface, implementation, verification, and license/risk.
2. Map the capability to local architecture primitives: owning module, adapter point, event/state boundary, permission surface, and fallback path.
3. Prefer absorbing the capability shape and verification method; copy implementation only when license, coupling, and maintenance risk are explicitly acceptable.
4. Land first as a local adapter/shim plus capability-registry entry, not as direct core mutation.
5. Add a harness: unit/integration smoke, demo fixture, failure case, rollback check, and any benchmark relevant to the claimed improvement.
6. Run in shadow/advisory mode before active control of a main workflow; compare success rate, latency, cost, error types, and regressions against the existing path.
7. Promote only behind feature flags / kill switches with rollback and preserved old behavior.
8. Ratchet the accepted pattern into a skill, ADR, project profile, or registry entry according to scope; do not put project-specific repo paths or one-off conclusions in global memory.

Decision heuristic:
- High value + high architectural fit + strong harness + low risk → adopt.
- High value + uncertain risk → spike then shadow.
- High value + high coupling/risk → absorb idea and rewrite locally.
- Low value + high complexity → reject/watch.

Red lines: do not let an external worker/tool gain decision authority without an explicit control-plane design; do not treat multi-model agreement as verification; do not drop existing behavior without a reversible rollout.

## Output Contract

For serious audits, produce:

```markdown
# Architecture Evaluation

## Objective
## Current Architecture / Component Map
## Theory or Principle Map
## External/Alternative Mapping (if any)
## Gap Analysis
## Prioritized Improvements
## Phased Plan
## Risks and Rollback
## Evidence Needed Before Landing
```

## Common Pitfalls

1. **Citing theory without implementation constraints.** A paper reference must change a design choice or verification gate.
2. **Feature comparison without architecture extraction.** Understand data flow and interfaces before scoring a framework.
3. **Making local edge workers smart.** In brain/tentacle designs, edge nodes execute and report; brain owns decisions and durable memory.
4. **Creating competing task pools.** Distributed executors should adapt to the canonical task/control plane unless explicitly designing a new one.
5. **Big-bang migration plans.** Prefer reversible phases with evidence after each slice.
6. **Over-formalizing small systems.** Match rigor to risk and team capacity.

## Verification Checklist

- [ ] Component map and interfaces are explicit.
- [ ] Theory/principle mapping is tied to concrete constraints.
- [ ] External framework value and migration difficulty are scored separately.
- [ ] Cloud/local state boundaries are named when applicable.
- [ ] Plan is staged, reversible, and evidence-gated.

## Support Files

- `references/architecture-theory-audit.md` — theory domain mapping and academic grounding details.
- `references/autonomous-runtime-governance-docs.md` — scoped reference for automation/control-plane architecture documentation: use for long-term, evidence-gated autonomous-runtime docs; anti-condition: do not use as task progress or a project-specific fact source.
- `references/external-framework-evaluation.md` — framework/tool evaluation template and scoring.
- `references/open-source-capability-absorption-governance.md` — evidence/rollback/maintenance promotion gates for absorbing open-source features into a local architecture.
- `references/cloud-edge-architecture.md` — brain/tentacle architecture, edge worker deployment, multi-node patterns, and pitfalls.
- `references/aws-mac-graphical-brain-deployment.md` — AWS EC2 Mac as an overseas graphical brain: cost modeling, GUI access, edge VPN separation, Tailscale/private overlay, security boundaries, and full-landing runbook artifacts up to paid-resource authorization.
- `references/cloud-macos-graphical-brain-vpn-edge.md` — overseas macOS graphical brain pattern: AWS EC2 Mac as GUI/Hermes executor, optimized VPS as VPN/edge relay, Tailscale/WireGuard as private control plane, with security and verification gates.
- `references/contextcard-mobile-assistant-stability.md` — ContextCard/mobile assistant long-term stability pattern: authority boundary, source-bound rich writer, polling watcher vs core hook decision gate, incremental merge/promotion invariants, fallback cache separation, and degraded multi-model review handling.
- `references/local-brain-canonical-architecture-absorption.md` — use when consolidating old Hermes local-brain artifacts (project profiles, SSOTs, ledgers, gate packets, receipts, phase docs) into a single canonical long-term architecture packet without creating patchwork docs or claiming runtime completion from documentation.
- `references/local-brain-auto-constraint-layer-landing.md` — use when landing a final local-brain auto-constraint-layer plan: fold auxiliary review capabilities back into the main SSOT, implement the first local dry-run BrainConstraintGate/RouteReviewGate slice with TDD, and keep runtime/external/lifecycle side-effect gates closed until separately authorized.
