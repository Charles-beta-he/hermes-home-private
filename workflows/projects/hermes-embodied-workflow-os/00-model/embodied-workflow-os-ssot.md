# Hermes Embodied Workflow OS — SSOT

Created: 2026-07-02T18:43:34+08:00
Status: `profiled + ledgered + research-backed architecture plan` (not runtime implementation)
Project id: `hermes-embodied-workflow-os`

## One-sentence objective
Build a stable, entry-agnostic, actor-agnostic workflow core for Hermes so Web/PWA/App/PC, glasses, voice, embedded devices, robots, NAS, proxy, and future physical tools attach as adapters instead of becoming separate assistant brains.

## Current diagnosis
Hermes already has a strong brain/CLI/tool substrate, plus adjacent projects for Agent OS, control console, mobile projection, and self-extension. The missing layer is the outer capability/adapter/workflow shell: stable contracts for observations, capabilities, action intents, evidence, telemetry, readback, and entry recommendation.

## Stable core, long-lived
- `WorkflowKernel`: owns session lifecycle and step progression.
- `TaskGraph`: machine-readable goals, steps, dependencies, preconditions, required observations, success criteria, and stop conditions.
- `Observation`: normalized input from Web upload, phone camera, glasses, voice transcript, fixed camera, robot camera, embedded sensor, or readback.
- `WorldState`: reducer-owned state derived from verified observations/evidence; adapters cannot write it directly.
- `Actor / Capability`: describes what a human, robot, embedded node, CLI tool, or external service can observe/render/execute/confirm.
- `Planner`: proposes `ActionIntent`, never executes directly.
- `SafetyGate`: evaluates logical/task/risk/authority constraints.
- `ExternalControlGate`: adds device identity, telemetry freshness, idempotency, audit sink, readback, and stop/escape requirements for physical/external actions.
- `ActionIntent`: the only executable command envelope.
- `Verification`: checks expected observation/result after a human or device action.
- `EvidenceLedger`: append-only evidence and decision ledger for replay/audit/debug/NAS archive.

## Variable/adapted layer
- Entry adapters: CLI, Web Workbench, PWA/App, PC Console, glasses, voice.
- Observation adapters: image upload, video sampler, first-person glasses, fixed camera, robot camera, sensor telemetry, ASR transcript.
- Actor/execution adapters: human manual operator, CLI tool, embedded node, robot, external-control device.
- Storage/network adapters: NAS archive/backup, Japan hot primary host, domestic proxy/tunnel.

## First vertical
Installation/assembly assistant is the first vertical because it exercises TaskGraph, observation, world-state estimation, action intent, safety, verification, and evidence. It must not be Web-specific. Web is a Workbench/debug/supervisor surface.

## Existing-project integration
This project composes existing Hermes-managed projects instead of replacing them:
- `hermes-agent-os-control-plane`: control-plane primitives: CapabilityGraph, Evidence DAG, AuthorityGate, route preflight.
- `hermes-control-console`: operator/Workbench/control-tower surface patterns.
- `mobile-offline-avatar-travel`: mobile/PWA/RN projection, light client, offline handoff and mobile authority boundary.
- `hermes-persona-wake-stage`: cross-end persona/wake/ritual interaction patterns.
- `hermes-self-extension-os`: mission/control-plane and review/fix/verify loops.
- `hermes-capability-model-router`: multi-model/surface routing, verifier specialization.

## Non-goals and hard boundaries
- No hardware or robot execution in this slice.
- No model-direct physical action ever.
- No Web/PWA/App/Glasses-specific branches inside Core.
- No NAS hot SQLite/WAL runtime.
- No proxy-layer business logic.
- No production/promoted claims without tests/readback/evidence.
- No cross-project secret/auth/session merge.

## Canonical artifacts
- Architecture: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/01-architecture/stable-core-and-adapter-architecture.md`
- Schemas: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/01-architecture/core-contract-schemas.json`
- Research/literature: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/02-research/core-works-and-arguments.md`
- Existing-project integration: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/03-integration/existing-project-integration-map.md`
- Roadmap: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/04-roadmap/phase-roadmap.md`
- Progress ledger: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/progress-ledger.md`
- Evidence index: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/02-research/evidence-index.json`
