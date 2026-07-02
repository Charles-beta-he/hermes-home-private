# ADR-0001 — Stable Core and Adapter-First Architecture

Date: 2026-07-02T18:43:34+08:00
Status: Accepted as architecture direction; not implemented as runtime code in this slice.

## Context
The user wants Hermes to grow from brain + CLI/tools into Web/PWA/App/PC, glasses, embedded, robot, NAS, proxy, and physical-world helper capabilities. A sequence of endpoint-specific minimal changes would create platform forks and unsafe execution paths.

## Decision
Adopt a stable core + adapter-first architecture. The stable core owns TaskGraph, Observation, WorldState, Actor/Capability, Planner, SafetyGate, ActionIntent, Verification, and EvidenceLedger. All entry and device surfaces attach through versioned ports and capability manifests.

## Consequences
- Web first implementation is Workbench/debug/supervisor, not product boundary.
- Assembly assistant is first vertical, not a Web-only product.
- Robot/embedded/physical systems are Actors/Capabilities behind ActionIntent and gates.
- NAS is archive/backup/evidence store, not hot runtime DB.
- Domestic proxy is transport, not business logic.

## Evidence
- Multi-model advisory review: `/Users/charles/.hermes/tick-20260702-101349-760163-p20773-dd66cf15-28477ee1/`
- Research evidence index: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/02-research/evidence-index.json`
- Existing project profiles read back in this session: Agent OS, Control Console, Mobile Platform, Self Extension.
