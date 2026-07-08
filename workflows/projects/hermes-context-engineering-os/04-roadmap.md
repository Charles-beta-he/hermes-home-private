# Roadmap and Reserved Extension Stages

## P0 — Local Foundation (safe, current slice)

Status: landed in this session.

- Project profile and SSOT.
- Context Packet schema/template/sample.
- Dependency-free lint script.
- Skill reference with core works.
- Evidence and boundary docs.

## P1 — Edge CLI first, runtime prompt only after cache-safe gate

Status: read-only Hermes repo inspection completed in `06-p1-runtime-target-analysis.md`; core runtime mutation not performed.

Decision:
- Prefer edge CLI/helper + skill routing first because Hermes AGENTS.md says prompt caching is sacred and core is a narrow waist.
- Direct system-prompt injection remains future/authority-gated.

Tasks:
- Candidate CLI: `hermes context packet lint <packet.json>`.
- Candidate CLI: `hermes context eval run <fixtures>`.
- Later, only with exact authority: add default-off `agent.context_engineering_packet_preflight`; test enabled/disabled/tool-unavailable paths and prompt-cache invariants.

## P2 — Context Regression Eval (standalone local harness)

Status: P2 local standalone harness landed. Core Hermes CLI integration remains future/authority-gated.

Landed tasks:
- Fixture set for pass/fail packet behavior.
- Expected behavior checks for unknown evidence id, missing do-not-save boundary, and missing authority readback.
- Standalone command: `python3 scripts/context_regression_eval.py`.

Future tasks:
- Add stale memory, over-broad authority, source laundering, and long-context pollution fixtures.
- Optionally expose through `hermes context-eval run` after Hermes core target and tests are authorized.

## P3 — Taskpool / Mission Integration (lifecycle boundary)

Authority needed: exact local board/mission/task IDs, idempotency key, readback command.

Tasks:
- Convert Context Packet into task intake fields.
- Attach evidence refs and negative cases to task records.
- Add proof gate before review->done.
- No force-done; no external dispatch.

## P4 — Dashboard / Control Room Projection (read-only UI boundary)

Authority needed: target dashboard surface and local browser verification.

Tasks:
- Read-only panel: Context Packet, Evidence DAG, Authority closed/open, Converge matrix.
- No executor buttons until separately authorized.

## P5 — Scheduler / Watchdog (cron boundary)

Authority needed: exact local-only no-agent cron target and script path.

Tasks:
- Silent-on-success watchdog for stale evidence or missing readback.
- Receipts only; no user messaging unless gateway target is explicitly supplied.

## P6 — External / Publish / Deploy / Broad Fanout

Status: closed.

Requires exact platform/target/payload, rollback/readback, and explicit authorization.
