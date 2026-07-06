# Personal AI OS UX Shell Projection

Status: read-only projection
Updated: 2026-07-06T14:55:00+08:00

This is a local UX shell projection, not a live dashboard claim. Every panel points to source artifacts and explicitly excludes unsupported runtime behavior.

## Panels

### Today
- Source: `13-mission-runtime-state.json`
- Shows: current stage `executing`, next action policy, stop conditions.
- Unsupported claim: no autonomous external execution.

### Missions
- Source: `13-mission-runtime-state.json`, `08-progress-ledger.md`
- Shows: Personal AI OS upgrade mission, evidence DAG, open boundary.
- Unsupported claim: no taskpool/mission lifecycle write executed by this projection.

### Inbox
- Source: `06-non-human-interface-boundary.md`, `13-mission-runtime-state.json`
- Shows: structured AuthorityBoundary/ExternalDependency records instead of generic human-intervention stop.
- Unsupported claim: no secret/payment/legal/hardware execution.

### Receipts
- Source: `11-authority-ledger-projection.jsonl`, git commits in root ledger.
- Shows: P0-P6 local authority/action records.
- Unsupported claim: no external payment/credential receipt.

### Permissions
- Source: `11-authority-ledger-report.json`, `06-non-human-interface-boundary.md`
- Shows: local grant scope, exact exclusions, sealed-secret handling.
- Unsupported claim: broad authorization does not become unbounded external authority.

### Data Vault
- Source: `12-data-vault-projection.json`
- Shows: D1/D2 project artifact classification, no raw secret export, no WIP global memory write.
- Unsupported claim: not a full OS secure enclave or cross-app data vault.

### Capabilities
- Source: `10-capability-projection.json`
- Shows: 299 projected nodes from skills/profile/local scripts, no execution.
- Unsupported claim: projected nodes are not automatically invoked.

### Risk Console
- Source: `06-non-human-interface-boundary.md`, `13-mission-runtime-state.json`
- Shows: stop conditions, external dependency boundaries, non-agent-typed secrets.
- Unsupported claim: no legal/payment/device risk is solved without external support.

### Model Console
- Source: `14-model-review-projection.json`, `04-multimodel-governance.md`
- Shows: model roles, RouteReview, EvidencePacket, local projection verdict, automation ceiling L3.
- Unsupported claim: no live multi-model fanout was executed in P6.

## Acceptance readback

- Every panel has a source artifact.
- Runtime/external/device/payment claims are explicitly bounded.
- This projection can be rendered by CLI/dashboard later without inventing product capability.
