# Automatic Semantic Knowledge Recall Integrity

## Applicability

Use this procedure when a governed task intake automatically retrieves local knowledge before execution and the retrieval receipt participates in lifecycle gating.

Use it for any task/control-plane system where retrieved knowledge must improve context without granting route, execution, side-effect, completion, multimodel, or durable-learning authority.

## Anti-conditions

- Do not use retrieved prose, titles, excerpts, scores, paths, or keyword matches as authority.
- Do not inject retrieved excerpts into worker instructions by default; persist bounded source references instead.
- Do not treat a self-consistent receipt as authentic merely because its duplicated fields agree.
- Do not require current-source verification for empty-result receipts; there is no source claim to verify.
- Do not use this pattern to authorize external writes, deploys, destructive operations, credentials, payments, or durable knowledge promotion.

## Contract

1. Accept only a validated, versioned semantic envelope.
2. Derive a deterministic bounded query plan exclusively from structured envelope fields.
3. Call retrieval through an argument-vector API, never shell interpolation.
4. Bound and deduplicate hits.
5. Persist only an allowlisted hit schema such as `path`, `heading`, `content_hash`, and `score`.
6. Require strict content hashes (normally 64 lowercase hexadecimal SHA-256 characters).
7. Exclude excerpts and retrieved instructions from the receipt.
8. Bind the receipt to `sha256(canonical JSON(envelope))`.
9. Persist context refs and proof/evidence refs separately from the semantic decision.
10. Gate executable lifecycle transitions with independent receipt validation.

## Brain concept/tag bridge

Local-brain note frontmatter `concepts` values are stable retrieval identifiers, not authority labels. Canonical task intake must bind explicit task `--concepts` into the validated semantic envelope as `concept_refs` before hashing, routing validation, and recall. Retrieval should query those exact concept IDs before broader outcome/capability terms. Keep the bridge bounded and fail closed: concept refs are unique slug-like identifiers, may not contain prose/whitespace, and cannot change lane, brain, execution, side-effect, learning, multimodel, or completion authority. Persist the enriched envelope so save/reload and lifecycle verification recompute the same query plan.

Producer invariant: direct intake and specialized wrappers may add explicit task concepts to the envelope only through the same canonical binding function. Update wrapper-forwarding tests to compare against the canonically enriched envelope rather than the raw caller JSON, while separately proving that generic/default concepts are ignored and no existing `concept_refs` are dropped or duplicated.

Verification must include a real-backend tag probe: choose known concept IDs from note frontmatter, assert those exact IDs lead the bounded query plan, and read back at least one matching note/atom by hash. Also test malformed whitespace/prose tags, duplicate tags, over-limit lists, save/reload equality, query-plan tampering, and unchanged authority projection.

## Per-turn memory-provider projection

When the same canonical index is exposed through a chat `MemoryProvider`, keep it separate from lifecycle-gated task recall:

1. Activate only through explicit provider configuration; provider discovery/installation alone must not enable it.
2. Implement `sync_turn()` as read-only retrieval and expose no write/tool schema unless a separately authorized write path exists.
3. Use an argument-vector subprocess/API call with a short timeout; process errors, malformed JSON, wrong top-level containers, or empty results return empty context rather than blocking chat.
4. Project a bounded allowlist (`path`, `heading`, strict hash, range/provenance, short normalized excerpt if the chat product requires it) and label the result `authority-neutral`: it is context, not instruction, permission, or proof of current external state.
5. Test the real `MemoryManager.prefetch_all()`/turn-prologue call path with the current user message; provider unit tests alone do not prove runtime wiring.
6. Read back configured provider status and one real non-empty query, then separately test timeout/error/malformed-output fail-soft behavior.

Hash-shape validation in the provider is only a projection guard. Canonical authenticity belongs to the source adapter/indexer (or an explicit current-source verifier); never claim that checking `64 hex` alone proves the excerpt is current or canonical.

## Lifecycle validation checklist

Before `claimed`, `running`, `review`, `certified`, or `done`:

- recompute the canonical envelope digest;
- recompute the exact query plan;
- validate receipt schema, status, and `context_only_no_authority` marker;
- reject unknown hit keys, malformed hashes, duplicate hits, fragment/newline path injection, and stored excerpts;
- derive context refs from hits and compare them with receipt refs;
- compare receipt refs with top-level task refs;
- require matching proof/evidence refs;
- for non-empty refs, query the current knowledge source and require every receipt `(path, content_hash)` pair to remain present;
- fail closed when source verification is unavailable, stale, malformed, or forged.

A digest stored beside mutable receipt data detects accidental drift but is not a trust boundary by itself. Current-source membership, an external append-only receipt ledger, or a cryptographic signer outside the mutable task record is needed to reject a fully recomputed forgery.

## Retrieval ranking pitfall

Top-k retrieval can be unstable across repeated searches when scores tie or indexes refresh. If intake stores a small per-query top-k, lifecycle source verification should search a wider bounded window and require the stored refs to be a subset of current results. It should not require the repeated top-k lists to be identical.

Example: intake may store two hits per query while verification searches ten per query. Keep both values bounded and test the real backend, not only a deterministic mock.

## TDD and verification matrix

Start with RED tests for:

- same envelope plus different body/title produces identical queries;
- different envelope fields change queries;
- recall error prevents task creation in strict intake;
- receipt cannot change semantic route or execution policy;
- excerpt/instruction fields are excluded;
- malformed hash and unknown hit keys are rejected;
- changed query plan or envelope digest is rejected;
- forged hits with internally consistent refs/evidence are rejected against the live source;
- source outage fails closed;
- existing `brain:`-style path prefixes do not become `brain:brain:`;
- frontmatter save/reload preserves the receipt object;
- event hooks observe only an already-persisted valid receipt;
- wrappers, inbox ingestion, and generated children all traverse the canonical intake function;
- force flags cannot bypass semantic or recall integrity gates.

Then run:

1. focused semantic/recall tests;
2. existing orchestrator and retrieval suites;
3. compile/lint/diff hygiene;
4. readiness selfcheck containing bounded, deduplicated, excerpt-excluded, authority-neutral, and source-verified assertions;
5. an isolated `TemporaryDirectory` lifecycle probe using the real retrieval backend;
6. negative real/mocked probes for forged source, bad hash, query tamper, and backend outage;
7. proof/memory replay gates;
8. independent verification against exact implementation hashes;
9. convergence-evidence readback before claiming scoped certification.

## Operational activation gate

Scope: any governed task store where automatic retrieval receipts participate in executable lifecycle gates.

Applicability: use after fixture/temporary-root certification when the operator asks whether the capability is actually active in the canonical live task store.

Anti-condition: do not run a live canary for mock-only work, or when canonical lifecycle mutation has not been authorized. This gate does not authorize business execution, external dispatch, credentials, deployment, or destructive effects.

Do not collapse implementation certification and live activation into one completion claim. A temporary-directory lifecycle proves code-path behavior only. Before saying the capability is operational, run one bounded canonical canary:

1. Create a uniquely named low-priority canary through canonical `add`, with event/worker execution disabled when testing persistence rather than dispatch.
2. Reload it from the canonical store and read back the receipt, context refs, proof refs, and rendered recall section.
3. Use normal lifecycle commands, without force, through at least `pending -> claimed -> running`.
4. Reverify current-source membership at the transition boundary.
5. Move the canary through an allowed terminal path and retain its audit record; if direct archival is illegal, inspect `next_allowed` and use a legal path such as `running -> expired -> archived`.
6. Read back derived views and final task state.
7. Report `implementation certified`, `live canary passed`, and `external/production deployment` as separate claims.

A rejected transition is not permission to use `--force`. Keep the canary free of business execution and unrelated side effects.

## Exact publication from a dirty control-plane checkout

Scope: publishing a bounded task-control feature from a repository with broad unrelated dirty state or branch divergence.

Applicability: the intended patch is known, but the primary checkout cannot safely be staged or rebased as a whole.

Anti-condition: do not use this pattern to publish unrelated local history, bypass protected-branch policy, or claim that a hook passed when it inspected different bytes.

Export the exact staged patch, apply it to a clean worktree rooted at the fresh remote target, and rerun tests against that remote-based artifact before commit/push. Include every test file that supports the claimed gate; tests executed from the dirty source tree do not prove that the staged or publish artifact contains those tests.

A shared pre-commit hook may be hardcoded to the primary checkout and therefore inspect unrelated dirty bytes from a clean worktree. Diagnose this as hook/worktree path drift: first attempt a worktree-aware invocation and record the exact failing test. If repository policy explicitly permits degraded publication, require equivalent exact-artifact tests, disclose any bypass, and route worktree-aware hook repair to follow-up engineering work rather than normalizing `--no-verify`.

## Claim boundary

Certification is scoped to the exact implementation bytes and local reversible behavior tested. It does not imply repository cleanliness, live activation, production deployment, external dispatch, historical proof-debt cleanup, or authorization for durable memory/Skill writeback. State which boundaries were crossed with fresh readback.
