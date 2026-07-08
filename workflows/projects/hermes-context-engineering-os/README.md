# Hermes Context Engineering OS SSOT

Status: active-local-ssot
Created: 2026-07-08

## Objective

Convert Context Engineering from research/trend into a governed Hermes capability: a Context Assembly Runtime that builds minimal sufficient context packets from objective, source evidence, selected skills, memory/profile, tool authority, execution observations, and verification requirements.

## Non-goals

- Not a blanket permission to change Hermes core runtime behavior.
- Not a vector-RAG-only project.
- Not a long-context dumping strategy.
- Not an external scheduler/gateway/taskpool executor without separate authority.
- Not durable memory for WIP status.

## Canonical Artifacts

- Research canon: `artifacts/context-engineering-canon.md` (external convenience copy: `/Users/charles/context-engineering-landing/context-engineering-canon.md`)
- Runtime diagram: `artifacts/context-engineering-runtime.html` (external convenience copy: `/Users/charles/context-engineering-landing/context-engineering-runtime.html`)
- Skill: `/Users/charles/.hermes/skills/context-engineering-os/SKILL.md`
- Project profile: `/Users/charles/.hermes/project-profiles/hermes-context-engineering-os.json`
- Context Packet schema: `schemas/context-packet.schema.json`
- Lint script: `scripts/context_packet_lint.py`

## Core Architecture

```text
Intent/Spec Gate
  -> Evidence Graph
  -> Knowledge Index
  -> Memory/Skill/Profile Router
  -> Tool & Authority Context
  -> Execution Loop
  -> Verification & Learning
```

## Success Criteria

1. A reusable Context Packet schema exists and can validate examples locally.
2. A research-to-runtime evidence brief exists with core works and claims.
3. A skill is installed and read-back verified.
4. Extension stages are pre-reserved with concrete boundaries.
5. No external, destructive, scheduler, production, or credential side effect is performed in this local landing slice.

## Current Authority Boundary

Allowed now: local reversible files, templates, scripts, skill support docs, read-only validation.

Closed until exact future authorization: Hermes core runtime wiring, taskpool lifecycle writes, cron enablement, external gateway dispatch, push/deploy/publish, credential handling, destructive cleanup.
