# Conversation Workspace OS implementation plan

Status: validated-local-slice
Canonical SSOT: `00-spec/conversation-workspace-os-ssot.md`

## Tasks

- [x] T1 — identify and preserve the existing stable project id.
- [x] T2 — define schemas/templates for handoff, claims, evidence and tmux manifest.
- [x] T3 — implement local-only stdlib CLI: `init`, `event-append`, `doctor`, `tmux-plan`, `tmux-reconcile`.
- [x] T4 — add deterministic tests for happy path, malformed state, overlapping claims, done-without-evidence, missing tmux and secret/authority rejection.
- [x] T5 — run temporary-project and live read-only smoke tests.
- [x] T6 — update profile, progress ledger and portfolio registry without overstating maturity.
- [x] T7 — run portfolio doctor/strict verify and scoped diff review.

## Current gate

The validated local slice keeps tmux execution, worker dispatch, Taskpool/Mission lifecycle write, external action, deploy, push, credential entry and destructive operation closed. Independent multimodel certification is also not claimed.
