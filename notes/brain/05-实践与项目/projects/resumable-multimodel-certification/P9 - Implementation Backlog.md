---
type: backlog
status: active
created: 2026-05-07
project: resumable-multimodel-certification
level: P9
---

# P9 - Implementation Backlog

## P0 — Contract and Audit

### RMCS-P0-001 Certification state enum

Define status values:

- `planning_only`
- `fanout_complete_uncertified`
- `discussion_partial_uncertified`
- `discussion_complete_not_certified`
- `discussion_complete_certified`
- `timed_out_uncertified`
- `degraded_uncertified`
- `corrupt_artifact_uncertified`

Acceptance:

- Missing `discussion_result.json` never returns certified.
- Existing tick with only `merged_plan.json` returns `fanout_complete_uncertified`.

### RMCS-P0-002 Tick artifact manifest

Create schema for:

- run manifest;
- planner outputs;
- discussion checkpoint files;
- final certification manifest.

Acceptance:

- Manifest validates complete and partial ticks.
- Sensitive fields are not persisted.

### RMCS-P0-003 `audit-certification <tick_dir>`

Read-only command returning certification status JSON.

Acceptance:

- No model calls.
- Runtime under 5s on recent ticks.
- Corrupt/missing files fail closed.

## P1 — Checkpoint and Resume

### RMCS-P1-001 Per-model checkpoint

Persist raw + parsed response after each discussion model call.

Acceptance:

- Killing process after a model response preserves that response.
- Parse failures are recorded, not discarded.

### RMCS-P1-002 Per-round summary checkpoint

Persist round input, votes, issue ledger delta, evidence requests, and status.

Acceptance:

- Round can be audited without reading terminal logs.

### RMCS-P1-003 `resume-discussion <tick_dir>`

Continue from cursor.

Acceptance:

- Does not repeat completed model calls unless `--force-rerun-model` is passed.
- Forced timeout test resumes to final artifact.

## P2 — Background-safe Runner

### RMCS-P2-001 Background status/heartbeat

Write heartbeat/status JSON during long discussion.

Acceptance:

- Stale heartbeat detected.
- Timeout is recorded as `timed_out_uncertified`.

### RMCS-P2-002 Cron-safe wrapper

Wrapper always emits non-empty JSON and uses process-group kill on timeout.

Acceptance:

- No cron empty response.
- Partial artifacts are preserved.

## P3 — Evidence-first Workflow

### RMCS-P3-001 Evidence request export

Export model evidence_requests as orchestrator work queue.

Acceptance:

- Evidence requests are deduplicated.
- High-severity unsupported claims block certification.

### RMCS-P3-002 Evidence refill state builder

Allow state to be rebuilt with verified evidence links.

Acceptance:

- Truth gate reports grounded before ratification.

## P4 — Optional parallelism

### RMCS-P4-001 Same-round parallel model calls

Only after checkpoint/resume/audit are stable.

Acceptance:

- Deterministic aggregation order.
- Provider concurrency budget respected.

## Deferred Backlog

### DEFERRED-TASKCREATE-RALPH

`TaskCreate -> 下一轮 ralph 入口自动串联` waits until RMCS P0-P2 are complete and self-check PASS.

Acceptance before reopening:

- audit-certification exists;
- resume-discussion exists;
- background runner exists;
- partial discussion cannot be certified;
- TaskCreate runtime fixture can be ratified using RMCS.
