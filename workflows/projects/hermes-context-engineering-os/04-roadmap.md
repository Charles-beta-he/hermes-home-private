# Roadmap and Reserved Extension Stages

## P0 — Local Foundation (safe, current slice)

Status: landed in this session.

- Project profile and SSOT.
- Context Packet schema/template/sample.
- Dependency-free lint script.
- Skill reference with core works.
- Evidence and boundary docs.

## P1 — Runtime Prompt / Context Packet Preflight (requires Hermes core repo work)

Authority needed: exact target repo/worktree and permission to edit Hermes runtime prompt assembly.

Tasks:
- Locate prompt-builder/context assembly path.
- Add default-off config flag, e.g. `agent.context_engineering_packet_preflight`.
- Inject compact packet guidance only for complex/high-risk tasks.
- Add tests for enabled/disabled/tool-unavailable paths.
- Verify built prompt/readback and prompt-cache invariants.

## P2 — Context Regression Eval (local tests, safe after repo target resolved)

Authority needed: permission to add tests/eval fixtures in Hermes repo or a standalone eval harness.

Tasks:
- Fixture set: stale memory, missing evidence, over-broad authority, source laundering, long-context pollution.
- Expected behavior: refuse/ask/tool-readback/context packet generation.
- CLI: `hermes context-eval run --fixture ...` or standalone script.

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
