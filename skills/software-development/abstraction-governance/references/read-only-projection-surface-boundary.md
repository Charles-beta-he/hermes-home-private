# Read-only Projection Surface Boundary

## Scope

Class-level governance pattern for any product/dashboard/control-room UI that displays a local automation/control-plane projection before execution authority exists. Applies to governed automation, mission boards, capability catalogs, authority ledgers, evidence graphs, and similar operator surfaces.

## Applicability

Use when the safe next slice is to expose state, evidence, or boundary records to an operator. The pattern is especially useful after a user authorizes continued progress but some downstream actions require external systems, credentials, legal/payment authority, or physical-device control.

## Pattern

1. Add a read-only projection API or adapter before building the UI.
2. Keep authentication/session protection unless the payload is truly public liveness data.
3. Normalize projection fields at the adapter boundary so false/safe states show as `no` rather than `unknown`.
4. Build the UI around operator questions:
   - What is working?
   - What evidence exists?
   - What boundaries are closed?
   - What external dependencies remain structured but non-blocking?
5. Make dangerous capability classes explicit as boundary rows: execution, lifecycle mutation, external dispatch, credential/secret handling, payment/legal action, and physical-device effects.
6. If a downstream capability is unsafe or unavailable, write a structured boundary/proposal/dependency record and continue with the next safe local projection/readback slice.

## Verification

- Unit/API test for projection shape and auth behavior.
- Frontend typecheck/build if a UI is added.
- Browser readback proving the route is non-blank and key sections render.
- Browser console check for JavaScript errors.
- Screenshot/vision readback for UI claims.
- Separate SSOT/ledger/backlog update when the project has a governance packet.

## Anti-conditions

Do not apply this pattern to justify silently enabling execution. A read-only status surface must not trigger scheduler/task lifecycle writes, tool execution, external messaging, secret reveal, payment/legal action, or device control. Those require their own explicit authority gate and target-state readback.

Do not store project-specific paths, branch names, commit IDs, or session outcomes in this reference.