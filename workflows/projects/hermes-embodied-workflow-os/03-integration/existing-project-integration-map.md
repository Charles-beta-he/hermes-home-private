# Existing Project Integration Map

## Purpose
Integrate current Hermes projects as modules/relations under `hermes-embodied-workflow-os` without merging secrets, runtime authority, or project-specific facts.

## Relations
| Existing project | Role in this project | Merge policy |
|---|---|---|
| hermes | Runtime brain/tool/gateway substrate | managed_by_agent_workflow; runtime contract only |
| hermes-agent-os-control-plane | CapabilityGraph, Evidence DAG, AuthorityGate, route preflight, side-effect governance | share governance/control-plane primitives only |
| hermes-control-console | Workbench/operator/supervisor surface patterns | operator surface projection patterns only |
| mobile-offline-avatar-travel | PWA/RN/mobile projection, light-client authority, handoff queue, offline evidence core | mobile entry patterns only; no travel facts |
| hermes-persona-wake-stage | cross-end wake/ritual/persona interaction patterns | interaction shell patterns only; no always-on authority |
| hermes-self-extension-os | mission/control-plane loop and review/fix/verify ratchet | execution-governance patterns only |
| hermes-capability-model-router | surface-aware model routing and verifier specialization | model routing patterns only |
| lark | external integration boundary example | no secret/auth merge |

## Consolidation rule
This is not a replacement project. It is an umbrella architecture/project memory that records how these projects combine into the outer tooling/body layer around Hermes.

## First reusable module extractions
1. `stable_core_contracts`: ActionIntent, Observation, CapabilityManifest, Verification, EvidenceLedgerEntry.
2. `adapter_port_boundary`: IngressPort, RenderPort, ExecutionPort, ArchivePort.
3. `dual_gate_external_control`: SafetyGate + ExternalControlGate.
4. `workbench_supervisor_surface`: Web/PC control tower as observer/approver/replay surface.
5. `light_entry_projection`: PWA/App/glasses as thin ingress/render/confirmation surfaces.
6. `data_topology_policy`: Japan hot primary, NAS archive/backup, domestic proxy transport-only.

## Boundary
Portfolio metadata and SSOT docs only in this slice. No source code, gateway config, cron, deployment, hardware, or external side effects are changed.
