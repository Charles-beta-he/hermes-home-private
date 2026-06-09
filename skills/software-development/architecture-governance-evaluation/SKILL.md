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
| Cloud-edge assistant design | Separate brain decision/state from local stateless execution; enforce auth, audit, allowlists, and centralized memory. |
| Architecture refactoring | Classify core/deprecated/integrated components, migrate essential features, then validate. |
| Distributed worker/task systems | Preserve a single task-pool SSOT; workers are execution-only unless a deliberate control-plane design says otherwise. |

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
- `references/external-framework-evaluation.md` — framework/tool evaluation template and scoring.
- `references/cloud-edge-architecture.md` — brain/tentacle architecture, edge worker deployment, multi-node patterns, and pitfalls.
