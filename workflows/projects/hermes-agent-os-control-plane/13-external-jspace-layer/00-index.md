# External J-space Layer — P0 Design Package

Status: p0-local-projection-skeleton
Project: hermes-agent-os-control-plane
Created: 2026-07-07

## Purpose

Translate Anthropic's J-space / Global Workspace insight into a Hermes-local, auditable external projection layer. This packet does **not** claim access to closed-model hidden states. It defines an external equivalent: workspace projection, evidence DAG, reflection readback, authority gates, and completion-claim downgrades.

## Canonical artifacts

- `specs/external-jspace-layer-v0.1.md` — P0/P1/P2 operating spec.
- `schemas/workspace_projection.schema.json` — minimal workspace projection contract.
- `schemas/evidence_dag.schema.json` — claim/evidence DAG contract.
- `schemas/completion_claim_packet.schema.json` — completion claim gate packet contract.

## Runtime-adjacent P0 implementation

- Script: `/Users/charles/.hermes/scripts/hermes_jspace.py`
- Tests: `/Users/charles/.hermes/scripts/test_hermes_jspace.py`

The script is local-file only. It creates workspaces under `~/.hermes/workflows/jspace/`, records evidence, checks P0 gates, emits reflection readbacks, and produces closure packets. It does not modify taskpool lifecycle, dispatch tools, send messages, publish, deploy, delete data, or read model hidden states.

## Current boundary

P0 is a local projection/evidence skeleton. P1 taskpool event bridge, P2 control room, and multi-model surface review remain design/backlog boundaries until separately implemented and verified.

## P1 local event projection

P1 now includes local projection-only `attach-task` and `on-event` commands in `/Users/charles/.hermes/scripts/hermes_jspace.py`. These commands write `event_ledger.jsonl` and map task lifecycle names to workspace states. They do not mutate the canonical taskpool/Kanban/Mission lifecycle.
