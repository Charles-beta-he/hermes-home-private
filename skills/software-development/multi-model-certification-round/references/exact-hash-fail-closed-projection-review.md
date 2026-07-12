# Exact-hash fail-closed projection review

**Scope:** Domain-level certification/code-review evidence for staged trust-boundary projections with backend and frontend consumers.

**Applicability:** Use when an independent reviewer is given an expected staged-diff hash and must test malformed data, reconciliation, and completion/certification overclaim.

**Anti-conditions:** Do not use when no immutable staged artifact is identified. Review authority does not permit editing, staging, committing, pushing, or repairing the slice.

**Falsifier:** Narrow this procedure if the workflow later supplies an immutable content-addressed patch bundle and first-class receipt/schema verification that supersede local staged-index evidence.

## Artifact gate

1. Read branch, status, staged filenames/stat, staged diff check, and SHA-256 of the binary cached diff before review.
2. Compare the digest exactly; mismatch means failed review rather than review of a nearby patch.
3. Separate staged files from unrelated unstaged changes.
4. Inspect the full patch and current implementation, tests, and interface/schema declarations.
5. Recompute digest and staged scope after tests/probes and bind the verdict to that final readback.

Check whether Git is using an alternate index. A stale temporary index may emit fatal object errors while a downstream digest command still hashes empty stdout. Treat any failed pipeline component as failed evidence, never accept only the final digest, and compare read-only against the canonical index when the alternate index is unexpected. Record which index produced the reviewed digest; some harnesses intentionally provide alternate indexes.

## Adversarial matrix

Probe relationships, not only field presence:

- malformed/non-object axes and entries;
- missing fields, wrong primitives, empty IDs, and booleans accepted as integers;
- negative counters and impossible aggregate bounds;
- aggregate-to-entry recomputation mismatch;
- duplicate canonical IDs;
- invalid entries filtered before recomputation;
- dependent eligibility after reconciliation removes a prerequisite;
- vacuous completion with zero required entries;
- certification overclaim without objective receipt evidence;
- frontend direct-consumer behavior under a crafted but type-shaped response.

Backend validation does not prove frontend defense-in-depth. Independently construct an all-green frontend payload with trusted/completion/eligibility/certification flags true but no independently verifiable receipt. A positive certification rendering is a logic/integrity blocker even if the backend currently strips that payload.

Also test frontend procedure-completion rendering independently of certification. Feed a type-shaped response whose aggregate claims completion while entries are empty, contain duplicate canonical IDs, or disagree with the aggregate. If the procedure card remains success/complete, the frontend has trusted a self-asserted aggregate instead of reconciling the entries and must fail review.

Beware masked tests: a certification-overclaim test can pass only because another axis remains degraded or incomplete. Add an isolated all-prerequisites-green/no-receipt case. Likewise, a completion-overclaim test must make every unrelated axis valid so the expected failure is caused by entry reconciliation rather than another degraded field.

Treat entry validation as an explicit compatibility matrix, not independent enum membership. Probe cross-field contradictions such as `implementation_state=missing|scaffolded` with fresh `e2e_failed`, or `implementation_state=missing` with `validation_state=stale` and `delivery_state=landed_unverified`. If these combinations survive filtering and an aligned aggregate remains trusted, report a logic blocker even when ordinary fixtures never emit them.

## Read-only adversarial probe pattern

Do not add temporary tests to the repository during an independent no-edit review. Exercise exported or pure private validators directly from stdin-driven interpreters when possible:

- For Python, invoke the repository-local interpreter with a stdin script that imports the validator and prints each compatibility-matrix result. Probe one contradiction per case so another invalid field cannot mask the target condition.
- For TypeScript modules containing erasable syntax and type-only imports, recent Node versions can run an stdin probe with `node --experimental-strip-types --input-type=module`. Import the projection builder and feed crafted all-green payloads directly. If unavailable, use the existing test runner without writing a fixture into the repository.
- Include isolated frontend probes for an all-green aggregate with empty entries, duplicate canonical IDs, and positive certification flags without a receipt. Capture the rendered value and tone as counterexample evidence.
- A negative test that passes only because an unrelated prerequisite remains degraded is masked evidence. Make every non-target prerequisite valid and vary only the condition under review.
- After build or typecheck commands, re-read `git status --short`; generated output may be ignored or tracked depending on repository configuration. The final digest/scope readback must prove the review itself did not alter the staged artifact.

## Subprocess, authority, and status-only trust boundaries

When the exact-hash slice wraps authorization, credentials, streaming output, or child processes, extend the adversarial matrix beyond ordinary unit tests:

- **Pin the whole authorized target.** Test every ambient app ID, domain, callback port, scope, root, and feature default. An environment variable may be unable to grant authority by itself yet still redirect or broaden an already-granted action. Grant-backed callers should pass exact allowlisted values and launch children with a minimal scrubbed environment.
- **Trace secrets across all channels.** Inspect argv, stdin, inherited environment, stdout/stderr, nested errors, URLs, and non-JSON payloads. Moving a secret from argv to stdin is incomplete if `Popen` inherits the parent variable containing the same secret; omission of `env=` means inheritance.
- **Split streaming sentinels at chunk boundaries.** A nonblocking `os.read()` fixes deadline blocking but introduces chunk fragmentation. Run URL/token extraction against a bounded rolling buffer and test every split point, not only complete-line output.
- **Probe delivery failures and reaping.** Exercise timeout, early leader exit, surviving descendants, kill races, and `BrokenPipeError` during stdin write/close. Every path must terminate the process group when necessary and reap the direct child.
- **Audit dependencies behind status-only claims.** Lock bytes/mtime may remain unchanged while an auth-store initializer creates encryption keys/directories, starts watchers, prunes expired records, or saves storage. Inspect the dependency implementation or compare all relevant state, not only the wrapper lock.
- **Use controlled fakes.** Fake credentials, mocked subprocesses, and harmless local process groups are preferred. Review authority does not permit real OAuth, external reads/writes, credential entry, or protected side effects.

At closure, recompute the canonical cached-diff hash and exact staged path set, verify target files have no unstaged overlay, and check residual processes. Avoid process-search self-matches with patterns such as `pgrep -fl '[l]ark-mcp login'`. Passing deterministic tests does not override a reproduced adversarial counterexample.

## Verdict

Run focused backend tests, the complete relevant frontend suite, typecheck/build when applicable, added-line security scans, and deterministic one-off probes. Do not modify repository files during independent review.

Fail closed on hash/scope drift, errored evidence commands, unresolved logic/security findings, unparseable evidence, or any completion/certification claim lacking its required independent evidence. Separate provider/runtime quorum, objective truth grounding, and final certification. Passing tests do not override a reproduced adversarial counterexample.