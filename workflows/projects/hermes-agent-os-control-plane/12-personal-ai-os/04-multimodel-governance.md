# Multi-model Governance for Personal AI OS

Updated: 2026-07-06T13:57:39+08:00

## Purpose

Multi-model use is promoted from ad-hoc consultation to an operating-system governance layer. Models are routed by role, risk, evidence needs, and certification gate.

## Model roles

- Implementer: code/scripts/tool execution planning; requires deterministic tests and readback.
- Architect: system decomposition, domain boundaries, long-term tradeoffs; requires conversion into executable slices.
- Visual/Spatial Reviewer: screenshots, UI, design, video, device/spatial observations; proves visual facts only.
- Safety/Adversarial Reviewer: risk, prompt/tool injection, permission expansion, privacy, P0/P1 dissent.
- Arbiter: resolves path choice against objective/cost function and evidence packet.
- T0 Router: low-cost classification, risk tiering, tool/model selection; cannot certify completion.

## RouteReview contract

Inputs:
- objective
- risk tier
- expected side effects
- data sensitivity
- available evidence
- required tools/services/devices
- candidate model roles
- budget/latency constraints

Outputs:
- selected model roles
- evidence packet requirements
- certification requirement
- dissent handling policy
- degraded mode policy
- automation ceiling

## Evidence Packet contract

A model review must receive a bounded packet, not free-form narrative:

- goal and success criteria
- constraints/red lines
- current state evidence
- changed artifacts/diff/logs/screenshots when present
- authority scope
- external dependency boundaries
- proposed claims with evidence IDs
- requested judgment schema

## Certification policy

- T0/T1 low-risk: single model + tool evidence may be enough.
- T2 local reversible code/config: implementer + reviewer + tests.
- T3 architecture/long mission/runtime governance: architect + reviewer + arbiter + evidence packet.
- T4 external write/publish/production/device: safety reviewer + exact authority + receipt/readback.
- T5 payment/legal/medical/credential: no autonomous execution; create sealed boundary/draft/decision packet only.

## Dissent policy

- P0/P1 safety/security/permission dissent blocks completion claim.
- Factual dissent triggers evidence lookup/readback.
- Architecture dissent triggers smaller reversible slice.
- Style/preference dissent is advisory.
- Provider unavailable means degraded certification; automation ceiling is reduced.

## Degraded mode

If a required model/provider is unavailable:

1. Preserve the old run as degraded; do not retroactively certify.
2. Continue safe local/read-only/reversible work where deterministic verification exists.
3. Do not promote high-risk runtime/external gates.
4. Create a reprobe task/packet for the exact provider path.
