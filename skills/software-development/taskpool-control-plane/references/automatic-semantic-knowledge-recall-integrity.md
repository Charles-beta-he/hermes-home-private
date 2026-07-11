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

## Claim boundary

Certification is scoped to the exact implementation bytes and local reversible behavior tested. It does not imply repository cleanliness, production deployment, external dispatch, historical proof-debt cleanup, or authorization for durable memory/Skill writeback.
