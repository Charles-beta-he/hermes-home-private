# Objective Model — Personal AI OS / Web4.0 Agent OS

Status: active
Updated: 2026-07-06T13:57:39+08:00

## Objective

Build Hermes toward a personal AI operating system aligned with Web4.0 Agent OS gaps, excluding only parts that require external ecosystem support. The system must prefer autonomous local progress over conversational handoff, while preserving authority, evidence, rollback, and user ownership.

## Success criteria

1. Goal-first interface: user goals route into missions/capabilities instead of ad-hoc chat-only execution.
2. Capability Graph: every tool/skill/service/device/model is projected with goal patterns, permission needs, risk, verification, rollback, and automation level.
3. Authority Ledger: every side-effect action has scope, grant, target, evidence, receipt, and rollback status.
4. Data Vault: personal/project data is classified by sensitivity, exportability, retention, and allowed use.
5. Mission Runtime: long-running goals have state, metrics, budget, open gates, evidence DAG, and next-action policy.
6. Multi-model Governance: model roles, route review, evidence packets, dissent, certification, and degraded mode are explicit.
7. Non-human boundary handling: missing authority/external support becomes a machine-readable boundary ticket, local simulation, draft, or receipt requirement rather than a generic “ask the human”.
8. UX shell direction: dashboard/CLI surfaces expose Today, Missions, Inbox, Receipts, Permissions, Data Vault, Capabilities, Risk, and Model Console.

## Hard constraints

- Do not type or store secrets, passwords, API keys, cards, OTP, seed phrases, or equivalent credentials.
- Do not claim external ecosystem readiness where DID/VC/wallet/payment/hardware/service contracts are absent.
- Do not mutate production systems, perform irreversible destructive operations, or broad external fan-out without exact target, rollback, receipt, and readback.
- Do not store WIP/task progress in global memory; use SSOT/profile/ledger artifacts.
- Do not treat multi-model agreement as truth without evidence-bound claims.

## Non-goals for this packet

- No real payment, contract signature, credential entry, or legal authorization implementation.
- No always-on camera/mic/location/sensor enablement.
- No external agent marketplace integration beyond local proposal schema.
- No deletion of historical Agent OS artifacts; this packet is a new canonical continuation layer.

## Cost function

Prefer: local, reversible, evidence-backed, schema-first, readback-visible, automation-enabling slices.
Avoid: broad runtime mutation without contract, hidden side effects, unbounded agents, external sends as proof, memory pollution, and UI claims not backed by runtime evidence.
