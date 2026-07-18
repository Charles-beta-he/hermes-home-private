# M³G 全记忆整合 Gate Readback — 2026-07-19

- canonical_design_doc: `/Users/charles/.hermes/docs/private/neural-modular-memory-architecture-20260719.md`
- implementation: `/Users/charles/.hermes/plugins/neural_modular_memory/`
- active_profile: `default`
- active_config_readback: `memory.provider=neural_modular_memory`
- architecture: one active MemoryProvider control plane + multiple canonical memory planes
- authority_boundary: local-only, authority-neutral, reference-only; no tool schemas; no external dispatch

## Deterministic verification

- Hermes venv: 39 tests, 0 failures, 0 errors, 0 skipped.
- Homebrew Python 3.14.3: 39 tests, 0 failures, 0 errors, 0 skipped.
- Repeat gate: 100 complete iterations × 39 tests = 3900 tests; 0 failures, 0 errors, 0 skipped; exit 0.
- `py_compile`: exit 0 for `store.py`, `provider.py`, and `test_memory_runtime.py`.
- scoped `git diff --check`: exit 0.
- production added-lines scan: hardcoded secret, `shell=True`, `eval/exec`, pickle and SQL-fstring findings all 0.
- `hermes config check`: exit 0.

macOS `/usr/bin/python3` is Python 3.9.6 and cannot import current Hermes code using `X | Y` type syntax. It is therefore not a supported second-interpreter gate; the second valid gate uses `/opt/homebrew/bin/python3` 3.14.3.

## Full-memory ownership and runtime closure

| Surface | Canonical owner | Integration result |
|---|---|---|
| `MEMORY.md` / `USER.md` | built-in memory tool | successful committed/non-staged writes append redacted immutable receipts only; no duplicate semantic projection or recall |
| Local Brain | canonical Markdown vault + `brainctl` derived index | retained as read-only canonical-document lane inside the single M³G provider; no second active provider |
| M³G | `neural_modular.sqlite3` | owns primary-turn L0 events, projections, scope, provenance, correction, consolidation, decay and activation telemetry |
| session history | `state.db` / `session_search` | remains historical source; no automatic full-history duplication into M³G |
| skills | skill directories / `skill_manage` | remains procedure owner; M³G procedure candidates cannot auto-promote |
| project profiles / SSOT / evidence DAG | governed project files | remains project-fact and acceptance owner; no automatic overwrite from M³G |
| compaction/current context | active runtime session | remains temporary working memory, not a canonical cross-session store |

Runtime closure evidence:

- `MemoryManager` still admits one external provider.
- primary-only turn, explicit-memory receipt and consolidation/decay maintenance writes are enforced.
- session switch updates the provider session before subsequent writes.
- Local Brain and M³G share one total recall budget.
- exact normalized duplicates prefer the Local Brain canonical citation only when that citation is actually injected; a Brain hit truncated out by budget cannot suppress the M³G claim.
- all recalled projections remain scope-, expiry-, status-, reference-only- and L0-provenance-gated.
- recall updates activation telemetry only and does not strengthen knowledge.
- decay is incremental per projection via `last_decayed_at`; repeated maintenance at one timestamp is idempotent and later runs apply only the new elapsed interval.
- `get_tool_schemas()==[]`.

## Built-in memory receipts and schema migration

- schema: `hermes.neural_modular_memory.v3`.
- `memory_write_receipts` supports `add`, `replace`, `remove` for `memory` and `user` targets.
- receipt content and nested metadata are redacted before persistence.
- receipt update/delete are rejected by SQLite triggers.
- receipts never enter events, projections, FTS or normal recall.
- v1/v2 projections migrate in place with nullable `last_decayed_at`; their existing strength is preserved on the first post-migration decay instead of applying historical age again.
- fixture v1→v3 migration retains existing L0 events and projection strength.

Live SQLite readback:

- `PRAGMA integrity_check=ok`.
- events: 4.
- projections: 10.
- edges: 16.
- activations: 15.
- memory_write_receipts: 0.
- `last_decayed_at`: column present; 10 migrated projections are NULL before their first v3 maintenance pass.
- immutable triggers: `events_no_delete`, `events_no_update`, `memory_write_receipts_no_delete`, `memory_write_receipts_no_update`.

Migration escape hatch:

- pre-v3 backup: `/tmp/neural_modular.pre-v3.20260719-033032.sqlite3`.
- SHA-256: `558fd1e6dcb2764e56d4b555b3f2216d51a5be0bfead5c2488724943f083352a`.
- backup schema/integrity: `hermes.neural_modular_memory.v2` / `ok`.
- pre-migration counts: 4 events, 10 projections, 16 edges, 15 activations, 0 memory-write receipts.
- the earlier verified pre-v2 backup remains retained as a deeper rollback point.

## Backup integration

The live Hermes backup collector loaded the active provider and returned:

- `BACKUP_EXTERNAL_PATHS=['/Users/charles/Documents/brain']`
- `ALL_EXIST=True`

This adds the external canonical Local Brain vault to the normal profile-local backup surface without physically merging it into M³G.

## Current implementation hashes before scoped commit

- `store.py`: `030c0652b9bdd48be7dad47d497acca6acc409ec280a8fd6cb673c8c43c47042`
- `provider.py`: `c5bd40c1992789674cc7a0f24edf0fe51f3529aa4179618d52c4f0d894303d8a`
- `test_memory_runtime.py`: `604e146094f350d346c9b58c314bc7122a5ebd03ee9e2b946dd642812a26ead5`
- `README.md`: `d7dea5a84c2e817924b2e8fe3107469eee9c1f65763f265c882a533dff4f7dea`

## Exact target and rollback

Exact commit allowlist:

1. `docs/private/neural-modular-memory-architecture-20260719.md`
2. `plugins/neural_modular_memory/README.md`
3. `plugins/neural_modular_memory/provider.py`
4. `plugins/neural_modular_memory/store.py`
5. `plugins/neural_modular_memory/tests/test_memory_runtime.py`
6. `workflows/projects/hermes-neural-modular-memory/06-projection/architecture-gate-readback-20260719.md`

The eight unrelated pre-existing stage-0 blobs must remain byte-identical before and after the scoped commit.

- runtime rollback: `hermes config set memory.provider localbrain`.
- code rollback: revert the exact scoped commit; never use global reset/clean in the mixed worktree.
- database rollback: preserve the active database for audit and restore only from the verified pre-v2 backup under a separate explicit recovery decision.
- `/tmp/hermes-memory-commit-repair.6B32FC` remains untouched.

## Certification boundary

This packet supports local implementation and deterministic verification only until a new immutable commit is created and an independent verifier returns a hash-bound verdict. Earlier verifier votes are historical and cannot certify this integration slice. Even a new PASS will not establish global certification, production recovery readiness, cross-device durability or long-horizon retrieval quality.
