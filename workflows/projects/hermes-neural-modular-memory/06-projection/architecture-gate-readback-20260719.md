# M³G Architecture Gate Readback — 2026-07-19

- canonical_design_doc: `/Users/charles/.hermes/docs/private/neural-modular-memory-architecture-20260719.md`
- implementation: `/Users/charles/.hermes/plugins/neural_modular_memory/`
- active_profile: `default`
- active_config_readback: `memory.provider=neural_modular_memory`
- authority_boundary: local-only, authority-neutral, reference-only; no tool schemas; no external dispatch

## Deterministic gate readback

- Hermes venv full suite: `Ran 23 tests ... OK`
- System Python full suite: `Ran 23 tests ... OK`
- Repeat gate: 100 complete iterations × 23 tests = 2300 tests; 0 failures, 0 errors
- `py_compile`: exit 0 for `store.py`, `provider.py`, `__init__.py`, and the test module
- `hermes config check`: configuration valid; active readback is `memory.provider=neural_modular_memory`
- provider discovery: discovered `True`, available `True`, loaded `True`
- live prefetch after same-session sync: 598 chars; authority boundary `True`; provenance `True`; within budget `True`; `get_tool_schemas=[]`
- SQLite: `PRAGMA integrity_check=ok`; 4 events, 10 projections, 16 edges, 12 activations
- immutable-event triggers: `events_no_delete`, `events_no_update`
- implementation hashes before scoped commit:
  - `store.py`: `84d14ab21772406cc0bea1363347060ee2613c9f10a3f8852f25e0bb4a818f0b`
  - `provider.py`: `20f863ee37c632b7edb8b901e0c4f43c88958c08177bc851f57abbe3b84c606a`
  - `test_memory_runtime.py`: `fb1e2bdb37331985dc4f399666368b195ceecbc65dcd3e5ac19ad04e3b3c44da`

## Independent verifier remediation map

The first independent verifier returned `FAIL` against an earlier drifting hash. Every concrete blocker and requested negative-test class was handled in the current slice:

- consolidation now rejects active `contradicts` edges;
- recall activation no longer promotes a single source to `supported`; two source events are required;
- `procedure`/`causal`/`decision` require direct same-event evidence in every supporting session before consolidation;
- same-scope unrelated correction regression remains covered;
- recall telemetry exception is explicit in the SSOT;
- primary and sibling recall share reference-only, expiry, scope, status, and provenance gates;
- Brain + modular recall share one total character budget;
- repeated `turn_key` with changed content raises `ValueError` instead of silently reusing an event;
- scope isolation covers session/task/project/user/domain plus global;
- brainctl timeout, non-zero exit, malformed JSON/hash/path/line fail closed;
- AWS key, cookie/session, card identifier, token, Authorization, and private-key patterns are redacted;
- automated test asserts `get_tool_schemas()==[]` and the authority-neutral prompt boundary.

A fresh independent verifier vote against the committed hashes remains required before any wording stronger than `locally_implemented_and_verified`.

## Exact target and rollback

- Exact commit scope: canonical design document, this gate readback, and `plugins/neural_modular_memory/` source/tests/docs only.
- Runtime rollback: `hermes config set memory.provider localbrain`.
- Code rollback: revert the exact scoped local commit; do not reset the mixed Hermes-home worktree.
- Database remains local at `/Users/charles/.hermes/memory/neural_modular.sqlite3` for audit.

## Certification boundary

This readback supports `locally_implemented_and_verified` only. It does not establish biological equivalence, production-grade certification, cross-device durability, long-horizon retrieval quality, external publication, or global certification.
