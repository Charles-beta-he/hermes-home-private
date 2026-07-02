# Stable Core + Adapter Architecture

## Architecture thesis
Do not build Web助手、眼镜助手、机器人助手 as separate products. Build one workflow core and many adapters. Every future entry or device must pass through typed ports, capability manifests, evidence, and gates.

## Layering

```text
L0 Domain contracts
  TaskGraph, Observation, WorldState, Actor, Capability, ActionIntent, VerificationResult, EvidenceLedgerEntry

L1 Runtime kernel
  WorkflowKernel, StateReducer, Planner, SafetyGate, ExternalControlGate, EvidenceLedger, ReplayEngine

L2 Registries
  AdapterRegistry, CapabilityRegistry, PolicyRegistry, SchemaRegistry

L3 Adapters
  CLI, Web Workbench, PWA/App, PC Console, Glasses, Voice, Camera, Embedded, Robot, NAS Archive, Proxy

L4 Deployment topology
  Japan host = hot primary runtime; NAS = archive/backup/evidence; mobile = light ingress; proxy = transport
```

## Port contracts

### IngressPort
Consumes external user/device input and emits normalized events/observations. It may authenticate, rate-limit, and redact, but it cannot mutate core state directly.

### RenderPort
Consumes Guidance/ActionIntent/Verification state and renders it to terminal, Web card, mobile UI, glasses voice/subtitle/overlay, or embedded display.

### ExecutionPort
Consumes approved ActionIntent only. It must support dry-run, idempotency, audit, readback, timeout, and fail-closed errors if it touches external/physical systems.

### ArchivePort
Copies evidence/artifacts to NAS or cold storage asynchronously. It must not become the hot runtime database path.

## Core anti-corruption rules
1. Core imports domain/runtime contracts only; adapters import core ports, not vice versa.
2. Platform names may appear in adapter manifests, not in Planner/SafetyGate/TaskGraph logic.
3. CapabilityRegistry answers “what can act/observe/render/confirm?”, not “what should happen?”.
4. Planner outputs ActionIntent; gates authorize or block; adapters execute only authorized intents.
5. WorldState is reducer-owned and evidence-linked.
6. Web Workbench is an observability/supervision tool, not the canonical runtime state.

## Required first contracts
- `CapabilityManifest`: capability id, actor id, adapter id, schemas, risk class, dry-run/readback/audit requirements.
- `Observation`: normalized visual/audio/sensor/text/readback input with evidence refs and derived facts.
- `ActionIntent`: executable envelope with preconditions, authority, risk, verification plan, idempotency, rollback/abort.
- `VerificationResult`: pass/warn/fail/blocked plus evidence and next-state effect.
- `EvidenceLedgerEntry`: append-only event/evidence/decision/receipt record.

## Entry recommendation
A future `EntryRecommendationEngine` should recommend the best entry based on required evidence/action, not platform preference:
- first-person detail -> glasses/phone camera
- long fixed observation -> embedded fixed camera
- complex editing/debug -> PC/Web Workbench
- fast confirmation -> mobile PWA/App
- low-risk local feedback -> embedded light/buzzer/display
- high-risk physical/electrical ->现场确认 + external-control gate, never blind remote execution

## Physical-world boundary
Physical or external actions require both gates:
1. `SafetyGate`: task/authority/risk/precondition evaluation.
2. `ExternalControlGate`: device identity, telemetry freshness, idempotency key, audit sink, readback method, timeout, stop/escape policy.

Dry-run/simulation is allowed early. Real actuation remains closed until exact target, rollback/stop path, and readback are implemented and authorized.
