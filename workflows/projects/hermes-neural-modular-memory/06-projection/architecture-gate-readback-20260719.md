# M³G 全记忆整合 Gate Readback — 2026-07-19

- canonical_design_doc: `/Users/charles/.hermes/docs/private/neural-modular-memory-architecture-20260719.md`
- implementation: `/Users/charles/.hermes/plugins/neural_modular_memory/`
- active_profile: `default`
- active_config_readback: `memory.provider=neural_modular_memory`
- architecture: one active MemoryProvider control plane + multiple canonical memory planes
- authority_boundary: local-only, authority-neutral, reference-only; no tool schemas; no external dispatch

## Deterministic verification

- Hermes venv: 45 tests, 0 failures, 0 errors, 0 skipped.
- Homebrew Python 3.14.3: 45 tests, 0 failures, 0 errors, 0 skipped.
- Repeat gate: 100 complete iterations × 45 tests = 4500 tests; 0 failures, 0 errors, 0 skipped; exit 0.
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
- receipt content, metadata dictionary keys, and nested metadata values are redacted before persistence.
- Luhn-valid 13–19 digit PANs are redacted in compact, space-separated, and hyphen-separated forms; compact/separated 12- and 20-digit runs remain intact rather than being partially redacted.
- receipt update/delete are rejected by SQLite triggers.
- receipts never enter events, projections, FTS or normal recall.
- consolidation validates claim/evidence provenance against immutable L0 hashes and its audit receipts reject update/delete through SQLite triggers.
- v1/v2 projections migrate in place with nullable `last_decayed_at`; their existing strength is preserved on the first post-migration decay instead of applying historical age again.
- fixture v1→v3 migration retains events, projections, edges, activations, FTS rows and projection strength, and reads back integrity plus immutable trigger inventory.
- unknown or future schema markers fail closed before migration DDL and remain unchanged on disk.

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

- `store.py`: `d0efb9d78d0ef5fa53f6c25c70461872ae2c5e66edd484c73c51d0f50886af40`
- `provider.py`: `c5bd40c1992789674cc7a0f24edf0fe51f3529aa4179618d52c4f0d894303d8a`
- `test_memory_runtime.py`: `14dc4a456f12d7c2d45b330412226edb08d6c572bed20503e111ee6813751c70`
- `README.md`: `455653bde7c5f56b14a89a9243311134d2dc3b614adac8a68d36eaafd6a256d7`

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

## 2026-07-19 post-release amendment: background-thread persistence and bounded runtime dependency

Independent adversarial review of remote commit `4aa5140481cff9f5397a3717f3fcc4331ee619f7` found two P1 blockers. This section supersedes that commit's earlier release gate; it does not retroactively certify it.

Root-cause evidence:

- `MemoryStore` created its SQLite connection on the initialization thread with SQLite's default thread affinity.
- `MemoryManager.sync_all()` executes `provider.sync_turn()` on its background executor; the provider intentionally catches storage failures to preserve the chat path.
- Exact RED reproduction returned `flush_pending=True` while a fresh database readback showed `events=0` and `projections=0`.
- A second RED test concurrently called `recall()` and `ingest_turn()` and raised `sqlite3.ProgrammingError` for cross-thread connection use.

Repair and negative evidence:

- `MemoryStore` now creates the connection with `check_same_thread=False` and owns one `threading.RLock`.
- Every public connection-bearing operation (`close`, memory receipt write, turn ingest, recall, consolidate, decay, stats and list projection/event access) holds that lock for the full operation/transaction; schema creation/migration additionally uses `BEGIN IMMEDIATE` plus bounded SQLite busy/locked retry so separate connections cannot race schema inspection and DDL.
- The real `MemoryManager.sync_all() -> flush_pending()` regression reads back two events and at least two projections from a newly opened store.
- The concurrent recall/write regression completes both futures and reads back four events.
- Plugin suite after repair and real-provider remediation: 51 tests, 0 failures/errors on Python 3.11 and Python 3.14; includes cross-thread persistence, concurrent recall/write, concurrent multi-connection schema initialization, observable background failure, canonical batch-receipt-to-provider mirroring, injected durable receipt-write failure, and fail-closed writes after store-initialization failure while recall remains fail-soft. The eight-connection migration regression repeated `20/20`.

Runtime dependency scope repair:

- The already-published outer baseline points to private runtime `f07ef1b9c5bfbf99478fd2a437cf59df851e5bf9`; the hotfix must not downgrade that dependency to the historical `fff5d19e...` pin.
- The final runtime remediation chain is five commits on top of that live private baseline: `1d0477fb0dc3103ea9f548d2806c14926f6d1037`, `5a5b66afe3322cfa9b0151cb21974337d485d5ee`, `48efdc01d74c112617af7aa5f97f99eedd5a407b`, `15f259fab11790527b7aadc9db672ebed9a50a79`, then `042a18ec41e8f631437c2eb08d17119a377b8281`.
- The exact range `f07ef1b9...042a18ec` remains limited to eight memory-lifecycle files: canonical mutation receipts, the `MemoryManager` durability/lifecycle gate, daemon-executor Python 3.14 compatibility, the two built-in memory-tool bridge call sites, and focused tests.
- Earlier candidates were invalidated by executable review counterexamples: duplicate add emitted a false receipt, a fake mixed top-level/batch shape masked the real batch ABI, shutdown could recreate its executor, provider close could exceed the drain deadline, canonical committed batches were not mirrored, executor-construction fallback could race provider shutdown, the real provider swallowed durable receipt-write failures, queued-prefetch failures bypassed the barrier, production bridge call sites discarded negative mirror acknowledgements without a warning, store-initialization failure falsely acknowledged turn and receipt durability, and separate SQLite connections raced `PRAGMA journal_mode` plus schema migration.
- Final remediation requires `success=true && changed=true`; canonical `committed_operation_indexes` for real batches; terminal submit-vs-shutdown state; propagation of durable provider receipt and initialization failures; recall-only fail-soft behavior; queued-prefetch failure accounting; explicit production warning on negative mirror acknowledgement with committed regression assertions; rejection instead of unsafe inline execution when executor construction fails; database-level migration serialization with bounded busy retry; bounded off-thread provider teardown; and a `flush_pending()` barrier that returns false for newly observed failures, rejected work, or a still-running shutdown drain.
- Pre-correction runtime gates on `15f259fab`: Python 3.11 and Python 3.14 memory-focused suites each produced `261 passed`; both production memory-dispatch paths produced `16 passed` on Python 3.11, including negative acknowledgement warning assertions; runtime failure counterexamples repeated `300/300`; real provider receipt success/failure cases repeated `200/200`; compileall and `git diff --check` passed. Repeated broad executions observed `5530` or `5531` passed with the same `125 failed, 37 skipped`, demonstrating order/global-state variance; no all-green claim is made. The unchanged live baseline had `5521 passed, 123 failed, 37 skipped`; those broad failures are known shared-state/log/registry order pollution.
- The outer hotfix points its gitlink to the live-baseline remediation tip, so this repair adds a five-commit scoped runtime chain rather than introducing or reverting the pre-existing private runtime history.

## 2026-07-20 post-publication correction: canonical receipt values

- A late exact-hash review of intermediate runtime `5a5b66afe3322cfa9b0151cb21974337d485d5ee` found that `committed_operation_indexes` selected the correct committed batch operations, but `MemoryManager` reconstructed their values from raw request bytes. `MemoryStore` strips `content` and `old_text` before committing, so a request such as `{"action":"add","content":"  canonical fact  "}` persisted `canonical fact` while the external receipt retained whitespace.
- The same executable counterexample remained valid at the published runtime `15f259fab11790527b7aadc9db672ebed9a50a79`; therefore the earlier exact-hash certification is superseded for canonical receipt-value parity even though its durability and lifecycle conclusions remain evidence for that immutable hash.
- Runtime `042a18ec41e8f631437c2eb08d17119a377b8281` normalizes mirrored `content` and `old_text` with the same strip semantics before calling providers. The real built-in batch regression was changed to submit whitespace-padded content and requires the provider receipt to equal the persisted canonical value.
- RED evidence on `15f259fab`: the targeted regression failed with provider content `"  new batch fact  "` versus expected `"new batch fact"`. GREEN evidence on `042a18ec`: bridge suites passed `17/17` on Python 3.11 and Python 3.14; the Python 3.11 focused slice passed `264` tests with `417` deselected; the Python 3.14 focused runtime slice passed `248` tests; the canonical batch counterexample repeated `300/300`; outer provider/plugin suites passed `51/51` on Python 3.11 and Python 3.14.
- This correction is source-only and local until a new hash-bound review/certification and ordered runtime-first/outer-second remote update are separately authorized and read back. It does not authorize deployment, activation, tags, releases, external dispatch or production rollout.

Exact rollback:

- Outer code rollback: revert only the hotfix commit after it exists; do not reset/clean the mixed main worktree.
- Runtime dependency rollback: restore gitlink `f07ef1b9c5bfbf99478fd2a437cf59df851e5bf9`; this removes the hotfix durability/error semantics and must only be used together with disabling `memory.provider=neural_modular_memory`.
- Operational disable: `hermes config set memory.provider localbrain`.

This amendment is deterministic local evidence. Push remains blocked until the minimal runtime commit is reachable from the private runtime remote, the exact outer candidate has clean full regression evidence, and an independent hash-bound verifier returns no P0/P1 blocker.

## Certification boundary

This packet supports local implementation and deterministic verification only until a new immutable commit is created and an independent verifier returns a hash-bound verdict. Earlier verifier votes are historical and cannot certify this integration slice. Even a new PASS will not establish global certification, production recovery readiness, cross-device durability or long-horizon retrieval quality.
