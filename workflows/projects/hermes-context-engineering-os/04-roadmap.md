# Roadmap and Reserved Extension Stages

## P0 — Local Foundation (safe, current slice)

Status: landed in this session.

- Project profile and SSOT.
- Context Packet schema/template/sample.
- Dependency-free lint script.
- Skill reference with core works.
- Evidence and boundary docs.

## P1 — Edge CLI first, runtime prompt only after cache-safe gate

Status: landed as local edge CLI. See `07-edge-cli-integration.md`.

Decision:
- Prefer edge CLI/helper + skill routing first because Hermes AGENTS.md says prompt caching is sacred and core is a narrow waist.
- Direct system-prompt injection remains future/authority-gated.

Landed tasks:
- `hermes context packet lint <packet.json>`.
- `hermes context eval run --root <project-root>`.
- Targeted tests: `./venv/bin/python -m pytest tests/hermes_cli/test_context_engineering_cmd.py -q` -> 5 passed.
- Real CLI readback against the SSOT sample and fixtures -> packet lint PASS, regression PASS checked=4.

Runtime-gated task status:
- Landed default-off `agent.context_engineering_packet_preflight` as a local CLI preflight projection, not runtime prompt injection. See `08-runtime-preflight-projection.md`.
- Tested disabled/enabled/missing-packet/invalid-packet behavior and verified `runtime_prompt_injection=false`, side effects closed, and no writes.
- Actual prompt assembly remains untouched; prompt-cache invariant tests are still required before any future injection into stable/context/volatile prompt parts.

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

Status: API and read-only UI projection landed. See `09-dashboard-api-projection.md` and `10-dashboard-ui-projection.md`.

Landed tasks:
- Read-only dashboard API: `GET /api/context/preflight?packet=<packet.json>`.
- Existing dashboard session-token auth protects the endpoint.
- Endpoint reuses the default-off preflight gate and preserves side-effect flags: no LLM, no writes, no runtime prompt injection.
- System page read-only panel with Context Packet path input, `Check preflight` button, gate/status badges, result counts, and side-effect readback.
- Tests, frontend typecheck/build, API smoke, browser readback, and console-error readback completed.

Remaining future enhancement:
- Optional richer Evidence DAG / Converge matrix visualization, still without executor buttons unless separately authorized.

## Certification Packet

- P1-P4 local engineering closure evidence is consolidated in `11-certification-packet.md`.
- Independent verifier vote is recorded in `12-independent-verifier-vote.md` with verdict `approve` and blockers `[]`.
- Current certification state: certified for bounded P1-P4 read-only Context Engineering preflight projection.
- Not certified: full product, full uIMax/A+ UI acceptance, runtime prompt injection/prompt-cache integration, agent loop mutation, taskpool/scheduler/external/publish/destructive surfaces.
- Remaining-scope authority/cooperation matrix is recorded in `13-authority-cooperation-matrix.md`; future not-claimed items must state what user cooperation is required.
- Targeted uIMax audit for the Context Engineering preflight panel is recorded in `14-uimax-targeted-audit.md`; result: `A- / local-operator-ready`, not full A+ dashboard certification.

## P5 — Scheduler / Watchdog (cron boundary)

Authority needed: exact local-only no-agent cron target and script path.

Tasks:
- Silent-on-success watchdog for stale evidence or missing readback.
- Receipts only; no user messaging unless gateway target is explicitly supplied.

## P6 — External / Publish / Deploy / Broad Fanout

Status: closed.

Requires exact platform/target/payload, rollback/readback, and explicit authorization.
