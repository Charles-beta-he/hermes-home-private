# Implementation Roadmap — Personal AI OS / Web4.0 Agent OS

Updated: 2026-07-06T13:57:39+08:00

## P0 — Canonical packet and schema projection

Goal: Make the target architecture durable and machine-checkable.

Deliverables:
- Personal AI OS SSOT packet.
- Domain model v0 JSON.
- Backlog with automation-first slices.
- Project profile pointer.
- Root progress ledger update.

Acceptance:
- JSON validates.
- Packet files read back.
- Profile points to packet.
- No runtime side effects beyond local file writes.

## P1 — Read-only Personal OS CLI/doctor projection

Goal: Expose packet state as a local read-only command surface.

Candidate implementation:
- Extend existing `hermes agent-os` surface or add `hermes personal-os status|doctor|schema`.
- Status reads project profile and packet files.
- Doctor checks required files, JSON validity, status fields, and boundary policy presence.

Acceptance:
- Focused tests pass.
- Live command returns ok true.
- No tool invocation, scheduler mutation, external send, or lifecycle write.

## P2 — Capability Graph projection v0

Goal: Project tools/skills/profile/service contracts into CapabilityNode records.

Candidate implementation:
- Local script or CLI command builds read-only capability projection.
- Includes automation level, side-effect level, data sensitivity, verification, rollback.
- Archived/profile-other skills excluded unless explicitly scoped.

Acceptance:
- Projection JSON generated.
- Doctor detects missing verification/rollback/permission fields.
- Sample route maps user goals to candidate nodes but does not execute them.

## P3 — Authority Ledger v0 for local actions

Goal: Side-effecting local actions produce receipts.

Candidate implementation:
- Receipt schema and writer for local file/code/config actions.
- Existing taskpool/mission/cron/gateway high-risk receipts mapped into AuthorityRecord shape.
- Broad vs exact authority fields explicit.

Acceptance:
- Disposable local write smoke creates authority receipt.
- Idempotency/readback works.
- External/payment/secret actions remain boundary records.

## P4 — Data Vault classification v0

Goal: Stop memory/profile/files from being treated as one undifferentiated context blob.

Candidate implementation:
- Local classifier/projection over memory/profile/project files.
- No raw secret export.
- D0-D6 classification and allowed_export field.

Acceptance:
- Profile and packet items classified.
- D5/D6 default export never.
- WIP entries are rejected from global memory target.

## P5 — Mission Runtime + Evidence DAG integration

Goal: Long-running goals run on state/evidence rather than chat memory.

Candidate implementation:
- Mission state schema aligned with existing mission/taskpool/cron.
- EvidenceNode projection from tests/logs/receipts/reviews.
- Next-action policy encodes non-human boundary replacements.

Acceptance:
- A sample Personal AI OS mission can tick locally and update evidence without external side effect.
- Boundary becomes AuthorityBoundary/ExternalDependency rather than chat stop.

## P6 — Multi-model Governance runtime preflight

Goal: Model routing/certification is a governed layer.

Candidate implementation:
- RouteReview and Evidence Packet builder.
- Review result schema.
- Degraded mode reduces automation ceiling.

Acceptance:
- Synthetic T3 architecture task produces bounded evidence packet.
- P0/P1 dissent blocks completion claim.
- Provider failure is recorded as degraded, not hidden.

## P7 — UX shell projections

Goal: Make personal AI OS state understandable to user/operator.

Candidate implementation:
- Dashboard/CLI views: Today, Missions, Inbox, Receipts, Permissions, Data Vault, Capabilities, Risk, Model Console.
- Start with read-only Markdown/JSON projections.

Acceptance:
- Each panel has a source artifact and no unsupported runtime claim.

## P8 — Device and external-agent proposal layer

Goal: Prepare Web4.0 endpoints without unsafe runtime expansion.

Candidate implementation:
- DeviceNode registry observe-first.
- AgentProposal inbox for subagents/external agents.
- ServiceContract registry for local tools/APIs.

Acceptance:
- External/subagent proposals cannot mutate lifecycle or send externally by default.
- Devices default to observe/draft unless exact safety gate exists.
