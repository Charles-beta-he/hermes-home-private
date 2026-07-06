# Non-human-interface Boundary Policy

Updated: 2026-07-06T13:57:39+08:00

## User directive

The user authorized full advancement and explicitly rejected using “人工介入” as the default interface.

## Interpretation

The system must not stop merely because a next step is ambiguous or requires stronger authority. It must transform the boundary into a structured artifact and continue all adjacent safe work.

## Boundary replacement mechanisms

1. AuthorityBoundary
   - Machine-readable missing authority record.
   - Includes action, target, risk, exact fields needed, rollback, receipt requirements.

2. ExternalDependency
   - Used when DID/VC/wallet/payment/hardware/service ecosystem support is missing.
   - Records provider, required standard, local simulation, and readiness check.

3. SealedSecretHandoff
   - For passwords/API keys/cards/OTP/seed phrases.
   - Agent does not type or store the secret.
   - System prepares form/command/context and records that secret entry is user-side or external secure-channel-side.

4. DraftThenAuthorize
   - For external messages/publishing/contracts.
   - Agent prepares payload, target binding, risk, rollback, and readback plan.
   - Execution requires exact target/payload authority or a pre-existing allowlisted gate.

5. LocalSimulation
   - For destructive/payment/device/external-agent actions where real target is unsafe or unsupported.
   - Use disposable canary or mock contract only; claim simulation, not production execution.

6. ContinueAdjacentWork
   - A blocked high-risk edge must not block schema, docs, tests, read-only projection, backlog, local doctor, or UX readback work.

## Prohibited interpretation

“Not using human intervention as interface” does not mean the agent may type secrets, invent credentials, bypass payments, forge legal authority, send unbounded fan-out, or execute irreversible production changes without exact target and receipt.

## Acceptance criteria

Every future boundary must be represented as one of:
- executable local action with receipt;
- AuthorityBoundary;
- ExternalDependency;
- SealedSecretHandoff;
- DraftThenAuthorize;
- LocalSimulation;
- explicit do-not-do safety invariant.
