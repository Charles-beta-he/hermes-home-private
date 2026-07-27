# Hermes Synthetic Journey Probe — SSOT v1

Status: locally-verified-candidate (independent review pending; not globally certified)
Project: hermes-agent-os-control-plane
Source pattern: Amazon CloudWatch Synthetics canary semantics, transferred as a provider-neutral Hermes capability contract; no AWS dependency.

## Objective

Prove a bounded Hermes journey by actively reading real local artifacts and checking business-level assertions, rather than inferring journey health from process/config presence.

## Non-goals

- No browser automation, model/API calls, external network, delivery, cron creation, taskpool/mission lifecycle mutation, repair, deploy, publish, credentials, or destructive action.
- No arbitrary shell/command adapter.
- No automatic memory, skill, experience-ratchet, or user analytics ingestion.
- A passing local probe does not certify global Agent OS health or production behavior.

## Capability contract

`SyntheticProbe` is a default-off, explicitly invoked local-read capability.

Inputs:
- versioned JSON probe declaration;
- project-root-relative regular JSON artifact targets;
- exact JSON-path assertions.

Outputs:
- stdout JSON receipt by default;
- optional exact local receipt path only when `--out` is supplied;
- artifact digests and assertion results, never source artifact bodies.

Allowed adapter:
- `json_readback`: bounded no-symlink read of one JSON artifact below the canonical project root, followed by typed equality assertions.

Forbidden effects are asserted in every receipt:
- external dispatch;
- scheduler, worker, taskpool, or mission lifecycle writes;
- model/LLM calls;
- memory or learning ingestion;
- arbitrary command execution;
- secret export.

## Acceptance criteria

1. Validation-only invocation returns `would_execute=false` and reads no journey target.
2. Explicit run over `06-projection/doctor_report.json` proves `ok=true` and `findings=[]` with target SHA-256 evidence.
3. Absolute paths, parent traversal, symlinks, oversized files, unknown adapters, malformed assertions, and assertion mismatch fail closed.
4. Receipts label `synthetic=true`, `exclude_from_learning=true`, and all forbidden side effects false.
5. No receipt file is written unless an exact `--out` path is supplied; output writes are atomic and constrained below this capability directory.
6. Unit tests cover positive, validation-only, mismatch, path escape, symlink, unknown-adapter, and explicit-output behavior.
7. Procedure validation may consume a projected `hermes_procedure_e2e_receipt_v1`, but registration does not imply global certification.

## Loop contract

- Objective: local synthetic journey probe contract + executable real readback.
- Baseline: this directory and current Agent OS doctor projection.
- Max iterations: 4 implementation/repair rounds.
- Repeated-failure limit: 2 per stable root cause.
- Authority ceiling: local write inside this capability directory; local read inside Agent OS project root.
- Stop: acceptance convergence, concrete tooling blocker, or a boundary requiring external/lifecycle/destructive authority.

## Converge matrix

| Claim | Required evidence |
|---|---|
| Contract is fail-closed | focused unit tests including negative cases |
| Real journey executes | CLI receipt against current doctor projection |
| No forbidden effects | receipt negative assertions + source inspection/tests |
| Default-off | validation-only receipt with `would_execute=false` |
| Provider-neutral | no AWS SDK/import/runtime dependency |
| Not globally certified | final report and procedure projection remain truthfully scoped |
