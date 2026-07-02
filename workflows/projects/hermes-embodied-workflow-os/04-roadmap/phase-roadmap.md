# Phase Roadmap

## P0 — Project memory and evidence pack (current slice)
Acceptance:
- Project profile exists.
- SSOT, architecture, literature/evidence, integration map, roadmap, ledger exist.
- Portfolio registry knows the project.
- Portfolio doctor still reports no errors.

## P1 — Contract-only core package
Deliverables:
- JSON schema or TypeScript/Python types for CapabilityManifest, Observation, ActionIntent, VerificationResult, EvidenceLedgerEntry.
- Static validator that rejects missing safety class/readback/audit on executable capabilities.
Acceptance:
- CLI mock, Web mock, glasses mock, embedded mock, robot mock can register manifests without core changes.
- Physical/external/destructive capability without gates is rejected.

## P2 — EvidenceLedger + reducer + replay harness
Deliverables:
- Append-only local ledger prototype.
- WorldState reducer consumes observations and verification results.
- Replay command regenerates session state from ledger.
Acceptance:
- Adapter cannot direct-write WorldState.
- Action completion claim requires evidence refs.
- Replay output matches latest WorldState snapshot.

## P3 — Web Workbench as first entry
Deliverables:
- Workbench views TaskGraph, WorldState, CapabilityRegistry, ActionIntent queue, EvidenceLedger, gate decisions.
- Manual approval/rejection emits events only.
Acceptance:
- Web contains no planner/safety core logic.
- Same session can be driven from CLI mock and inspected in Workbench.

## P4 — Assembly/install vertical as pilot
Deliverables:
- Manual -> TaskGraph ingestion or hand-authored TaskGraph.
- Human actor and mock robot actor consume same ActionIntent.
- Image upload/first-person mock observation path.
Acceptance:
- Web upload and glasses mock image use same Observation path.
- Text input and ASR mock transcript use same user-intent path.
- Uncertain visual evidence requests a better view instead of hallucinating.

## P5 — Mobile/PWA/glasses light entries
Deliverables:
- PWA/App: photo, voice transcript, confirmation, short status.
- Glasses: look/record/next-step receipt flow.
Acceptance:
- No canonical facts from mobile/glasses; they submit observations/confirmations only.
- Missing media receipt blocks visual claims.

## P6 — Embedded observation, then low-risk feedback
Deliverables:
- Fixed camera/sensor/button/status-light manifests.
- Dry-run pan/tilt/light/buzzer actions.
Acceptance:
- Heartbeat/readback recorded.
- Edge node fails closed on disconnect.

## P7 — ExternalControl low-risk real actions
Deliverables:
- ExternalControlGate dry-run then exact low-risk action packet.
- Telemetry freshness, idempotency, audit, readback.
Acceptance:
- Only status light/buzzer/display/camera pan/low-voltage light class allowed initially.
- No locks, heating, mains, high-power, gripper, cutter, or robot arm motion.

## P8 — Robot actor limited subset
Deliverables:
- RobotCapabilityManifest and robot observation/readback schemas.
- Dry-run robot plan consumer.
Acceptance:
- Robot is Actor, not a new brain.
- Every action has bounded workspace, stop condition, and verification.
