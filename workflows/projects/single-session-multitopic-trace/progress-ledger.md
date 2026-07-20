# Conversation Workspace OS Progress Ledger

Project ID: `single-session-multitopic-trace`
Display name: `Hermes Conversation Workspace OS`
Canonical SSOT: `00-spec/conversation-workspace-os-ssot.md`
Current maturity: `validated_local_control_plane_slice_no_multimodel_certification`

## Preserved scope

The original single-session multitopic trace/query direction now has a validated local read-only query artifact (`E-WSO-008`). The stable project ID remains preserved, and chat/session history remains a non-authoritative projection below the Project SSOT.

## Validated local slice

- Non-overwriting project initialization.
- Separate direction/task/worker/chat state domains.
- Append-only JSONL events with `flock`, flush and fsync.
- Cross-process project-state lock serializing claim, handoff and evidence read/check/write transactions.
- Bounded write/review/read claims with existing-worktree checks, 1-1440 minute TTL enforcement and project-relative scope validation.
- Single writer per direction and conservative static-scope overlap rejection.
- Idempotent claim release, handoff intake and evidence intake.
- Secret-like and authority-smuggling field rejection.
- Immutable evidence indexing with SHA-256 verification.
- Read-only doctor with negative requirements.
- Tmux full-plan and additive reconcile output with `executed=false`.
- Tmux manifests cannot carry worker commands.

## Fresh evidence

- `E-WSO-001`: initial 14 focused unittest cases passed.
- `E-WSO-002`: live project doctor returned 0 errors / 0 warnings before profile convergence.
- `E-WSO-003`: degraded multimodel packet; independent reviewers unavailable, certification explicitly withheld.
- `E-WSO-004`: Portfolio strict verify `ok=true`, zero errors; two unrelated pre-existing profile-only warnings.
- `E-WSO-005`: Portfolio semantic audit `ok=true`, 100% declared-dimension coverage, target project verdict `pass`; one unrelated warning remains.
- `E-WSO-006`: 15 focused tests passed after adding a deterministic concurrent-claim serialization probe.
- `E-WSO-007`: 16 focused tests passed after adding bounded TTL and project-relative scope traversal rejection.
- `E-WSO-008`: read-only local Hermes session query resolved prior same-project context without promoting chat to canonical state.
- `E-WSO-009`: isolated Hermes-session handoff was persisted and read back under a bounded review claim; the claim was then released.
- `E-WSO-010`: post-pilot final doctor returned 0 errors and 0 warnings after claim release.
- `E-WSO-011`: fresh Portfolio strict verify returned 0 errors and semantic audit kept the target project at 100% covered/pass.

## Current hard boundaries

No tmux execution, worker execution, Taskpool/Mission lifecycle write, external dispatch, deploy/push, credential entry, destructive action or model-vote completion authority is open.

## Remaining promotion gates

1. Independent multimodel certification after providers recover.
2. Separate exact authorization before any runtime execution or Taskpool/Mission integration.
