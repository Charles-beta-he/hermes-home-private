# Direction — Multi-session fusion and tmux workspace

State: validated-local-pilot

## Goal

Fuse independently advancing chat sessions through canonical handoffs, claims, evidence and decisions while keeping tmux as a replaceable execution workspace.

## Implemented local slice

- Canonical SSOT and distinct state domains.
- Non-overwriting project initialization.
- Append-only JSONL events with file locking and fsync.
- Cross-process state mutation lock for claims, handoffs and evidence indexing.
- Write/review/read claim acquisition and release.
- Conservative overlapping-scope rejection.
- Safe handoff/evidence intake.
- Read-only doctor and plan-only tmux reconstruction.

## Closed gates

No tmux execution, worker dispatch, Taskpool/Mission mutation, external write, deploy, push, credential entry or destructive action.

## Validation evidence

- `E-WSO-007`: 16 focused tests passed.
- `E-WSO-009`: an isolated Hermes source session ran fresh tests and doctor, produced a bounded handoff packet, and the receiving session persisted and read back the canonical packet before releasing its review claim.
- The source packet retained the expected missing-tmux warning and explicitly prohibited promotion of chat, tmux or model output to canonical completion.

## Remaining certification gate

Independent multimodel certification remains unavailable and is not implied by this local pilot.
