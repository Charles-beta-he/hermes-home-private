# Exact staged-artifact verification under concurrent mutation

## Applicability

Use when a requester names an expected staged-diff hash, restricts review to staged files, forbids changes to files/index, or another process may stage fixes during verification.

Anti-conditions: a normal review of a stable branch with no exact-artifact requirement, or work where an isolated worktree/index may be created and certified instead.

## Artifact identity gate

A verdict certifies one immutable artifact—not whatever happens to be staged at closure. Bind each finding and test result to the initial cached binary-diff hash and stage-0 blob IDs. If the live index changes, fail closed and report the reviewed and final-live hashes separately.

Run Git commands against the intended index, never an accidentally inherited one. For the real index, unset `GIT_INDEX_FILE`; for a requester-supplied alternate index, prefix every command with its exact absolute path. In both cases set `GIT_OPTIONAL_LOCKS=0` **from the first Git read onward**: nominally read-only commands can otherwise refresh index stat-cache metadata and change the index-file checksum, violating a no-index-modification contract even when entries and the cached diff remain semantically unchanged.

```bash
# Real index
env -u GIT_INDEX_FILE GIT_OPTIONAL_LOCKS=0 git diff --cached --name-status
env -u GIT_INDEX_FILE GIT_OPTIONAL_LOCKS=0 git diff --cached --binary | shasum -a 256
env -u GIT_INDEX_FILE GIT_OPTIONAL_LOCKS=0 git ls-files --stage -- <target-files>
env -u GIT_INDEX_FILE GIT_OPTIONAL_LOCKS=0 git diff --cached --check

# Exact alternate index supplied for review
GIT_OPTIONAL_LOCKS=0 GIT_INDEX_FILE=/absolute/path/to/index git diff --cached --name-status
```

Before the first Git command, checksum the index file directly. In one identity envelope, capture: index checksum before, cached binary-diff hash, ordered scope, mode/blob IDs, then cached hash and index checksum after. If the checksum changes, report it even when the patch hash is unchanged; if entries/scope/hash also change, classify material `ARTIFACT_DRIFT` immediately. Do not let subsequent green tests retroactively certify the initial artifact.

Record ordered name/status scope, mode/blob ID for each target, and any unstaged target deltas. Inspect recorded blobs (`git cat-file blob <oid>`) rather than an unpinned worktree path. Recorded blob IDs remain valid evidence if the index moves.

**Keep blob inventory scoped.** Never run bare `git ls-files --stage` for an exact-artifact review: on a large index it emits the entire repository, obscures the reviewed identities, and can overflow or truncate evidence capture. First obtain the ordered changed paths with `git diff --cached --name-only`, then invoke `git ls-files --stage -- "$path"` for each recorded path. Preserve that exact scoped list for the pre/post comparison.

## Python stale-bytecode trap

`PYTHONDONTWRITEBYTECODE=1` and `python -B` prevent new bytecode writes but do **not** ensure existing `.pyc` files are ignored. A timestamp/size-valid stale cache can make tests or `importlib` probes execute code different from source or staged bytes.

For exact-artifact probes:

1. Prefer loading the recorded Git blob and `compile(source, pinned_filename, "exec")` into an in-memory module.
2. If path-based imports are unavoidable, use a fresh `PYTHONPYCACHEPREFIX` plus disabled writes, then verify a source sentinel or loaded function body before trusting the run.
3. A suite run after index drift is evidence only for the new live artifact.
4. Passing tests never cure a hash mismatch.

## JavaScript/TypeScript isolated dependency setup

A staged snapshot may not contain `node_modules`, and borrowing the source worktree's dependency directory can accidentally couple the run to mutable local state. Prefer a fresh snapshot-local install when the lockfile is available:

1. Materialize the copied-index snapshot first and verify its scoped binary-diff hash/blob IDs.
2. Run the repository's lockfile-enforcing install (`npm ci`, `pnpm install --frozen-lockfile`, or equivalent) inside the disposable snapshot. Use `--ignore-scripts` when lifecycle scripts are unnecessary for the focused tests and would expand side effects.
3. Run the focused test runner from that snapshot so module resolution uses snapshot-local source and dependencies.
4. Recompute the alternate-index checksum, scoped hash, scope, and blob IDs after installation/tests. Dependency installation must not affect the pinned Git identity.
5. If an initial run is blocked only because dependencies are absent, classify it as harness setup, create a fresh materialization, install dependencies there, and rerun the full pre/test/post identity envelope. Record the blocked attempt separately; do not call it an artifact failure.

Do not certify an unstaged or excluded lockfile merely because it was used to provision the disposable harness. Report separately whether the lockfile is in the reviewed staged scope.

## Atomic test-identity envelope

Do not separate “record index identity,” “materialize the snapshot,” and “run tests/probes” into unrelated commands when concurrent staging is possible. Otherwise a later green run cannot be attributed confidently to the initial hash.

For every isolated test or counterexample run:

1. In the same command/process, read the supplied alternate-index checksum, cached binary-diff hash, ordered scope, and target blob IDs.
2. **Copy the supplied index byte-for-byte to a private temporary index, verify the copy checksum equals the supplied checksum, and materialize only through the copied index.** Never run `git checkout-index`, `git read-tree`, or another index-aware materializer with `GIT_INDEX_FILE` pointing at the requester-supplied index: even with `GIT_OPTIONAL_LOCKS=0`, such commands can rewrite stat-cache/extension bytes while leaving the cached diff, scope, and blob IDs unchanged.
3. Materialize with `GIT_INDEX_FILE=<private-index-copy>` into a temporary checkout; then remove `GIT_INDEX_FILE` from all test children.
4. Run the tests/probes against the materialized tree, using a fresh bytecode/cache location.
5. Before returning the result, recompute both identities: (a) supplied-index checksum/hash/scope/blob IDs and (b) private-copy checksum/hash/scope/blob IDs. Print pre/post values with the test result.
6. If the supplied index checksum changes at all, classify the review run as `REVIEW_BOUNDARY_VIOLATION` (and as `ARTIFACT_DRIFT` too when entries/scope/hash/blobs changed). Do not issue PASS merely because the semantic diff identity stayed stable. If only the private copy changes, discard the harness and rematerialize from a fresh copy before trusting tests.

Minimal safe materialization pattern:

```bash
supplied=/absolute/requested.index
private="$tmp/index.copy"
cp -p "$supplied" "$private"
test "$(shasum -a 256 "$supplied" | cut -d' ' -f1)" = \
     "$(shasum -a 256 "$private" | cut -d' ' -f1)"
GIT_OPTIONAL_LOCKS=0 GIT_INDEX_FILE="$private" \
  git checkout-index --all --prefix="$physical_root/.hermes/"
# Tests must not inherit either index.
env -u GIT_INDEX_FILE HOME="$physical_root" ...
```

For very large repositories where `checkout-index --all` is disproportionate, a bounded materialization is acceptable only when dependency closure is explicit: archive the immutable `HEAD` baseline for every source/test/config tree the focused commands can load, then overlay every changed path from the private index copy. Run from that disposable tree with `GIT_INDEX_FILE` removed. If imports, discovery, generated inputs, repository-root configuration, or test selection can reach outside the archived trees, broaden to a full materialization; a guessed partial snapshot cannot certify the artifact.

If pre/post identity differs, keep findings against recorded old blob IDs as evidence, but do not certify either artifact.

When tests hard-code `Path.home()` or paths under `~/.hermes`, preserve that layout in the isolated snapshot: materialize the repository at `<physical-temp-root>/.hermes/`, set `HOME=<physical-temp-root>`, and run from `<physical-temp-root>/.hermes/`. Merely setting `HOME` to a checkout rooted at `<temp>/` makes such tests look for `<temp>/.hermes/...` and yields harness-only `FileNotFoundError` failures. On macOS, canonicalize the temporary root with a physical path (`pwd -P` or equivalent) before using it: `/tmp` commonly resolves through the `/tmp -> /private/tmp` symlink, so a correctly strict all-ancestor symlink validator will reject a logical `/tmp/...` test fixture. This is a harness-path issue, not a reason to weaken symlink rejection.

Use an interpreter that actually provides the project test runner, but classify interpreter discovery/setup failures as harness setup rather than artifact findings. After correcting the harness, rerun the complete exact-snapshot envelope from a fresh materialization. Ensure the envelope reports post-run index/hash/scope/blob identity even when tests fail (for example via a cleanup/finalization trap); a fail-fast shell that exits before post-identity readback leaves the failed run unattributed.

For acceptance criteria that name fail-closed counterexample classes, do not rely only on aggregate pass counts. Run focused named tests or direct pinned-byte probes and print the decisive returned state—for example `invalid_registry` plus `can_claim_complete=False` for count mismatches and bool-as-int inputs—then run the broader suite separately.

If drift is detected after a semantic finding, reproduce the finding from the recorded old blob IDs with `git cat-file blob <oid>` plus in-memory `compile`/isolated loading. This binds the counterexample to the original reviewed artifact even when the live index has moved.

## Deterministic TOCTOU probes

Do not rely on probabilistic race loops. Load the pinned blob in memory and inject a controlled transition between the exact read and later validation. The reproduction should prove that bytes came from a forbidden inode/path state, the later check observed a different allowed state, and the function accepted the earlier bytes. Keep repository files and index untouched.

## Secret-boundary probe

When the contract says the child environment is secret-free, testing only named application variables is insufficient. Mock/capture the exact `Popen(..., env=...)` boundary and seed an unrelated sentinel secret. Verify separately:

- application secret absent from argv;
- application secret absent from child environment;
- unrelated ambient secret absent from child environment;
- public stdout/stderr contains no secret or raw child output.

If arbitrary ambient entries survive, report the exact contract failure. Prefer a minimal environment allowlist over a denylist when compatible with the child contract.

## Fail-closed contract probes beyond happy-path tests

For exact staged reviews of validators, registries, receipts, or control-plane projections, compile/load the pinned staged blob in memory and probe malformed values directly. Green suites often miss cross-field and coercion failures.

Required probe classes:

1. **Validate-then-coerce crash:** If validation records an invalid numeric/string field, later evaluation must not still call `int(...)`, `str(...)`, or another coercion that can throw. Return an invalid/fail-closed state rather than crashing. Probe the aggregate evaluator as well as the field validator: a validator may correctly report `invalid_freshness_seconds` while a later unconditional `int(value)` still raises before the invalid state can be projected.
2. **Boolean scope escape:** Fields such as `required`, `enabled`, `trusted`, `complete`, and `promoted` must require actual booleans where the schema says boolean. Never use `bool(untrusted_value)` at a scope or certification boundary: `0`, `[]`, and `""` can silently remove required scope, while `"false"` is truthy. Probe the final aggregate/certification result, not only declaration issues: malformed `required: 0` can disappear from the required set and make an empty required set appear complete.
3. **Cross-field invariant contradiction:** Validate implications, not only field types. Examples: `can_claim_complete => inventory_complete`; `certified => evidence_complete`; `promoted => no blocking findings`; final receipt status must agree with independently recomputed issues. Reject syntactically valid but contradictory projections as untrusted.
4. **Counter contracts:** Require integers, reject booleans (Python booleans are integers), reject negatives, and check count relationships where they carry semantics—not only individual field types.
5. **Lifecycle audit continuity:** Exercise at least two sequential transitions. A single-transition test can miss overwriting `previous_state` or other audit metadata on the next demotion/reopen. Verify append-only history and no implicit promotion independently.

Use the smallest deterministic counterexample and report its exact returned object or exception. A material fail-open or crash is sufficient for `BLOCK`; unrelated passing test counts do not outweigh it. When filesystem fixtures are unnecessary, keep probes read-only by loading staged source via `git show :path` and `compile(...)`.

## Cross-language trust-boundary parity probes

Applicability: staged artifacts that project one trust or completion decision through a dynamically typed backend boundary and a browser/client boundary. Anti-condition: ordinary display-only data with no trust, completion, eligibility, certification, or security consequence.

When the staged slice projects one trust decision through backend and client layers, green per-language suites are insufficient. Probe malformed runtime values at each consumer boundary and compare whether both layers fail closed.

1. **Require literal booleans at the final decision site.** Compile-time client types disappear at runtime. Do not use truthiness for trust/certification fields (`trusted_read_only && ...`, `Boolean(untrustedValue)`, or `if (status.trusted)`). Require `value === true`. A string such as `"false"` is truthy and can otherwise promote an untrusted projection to a success state.
2. **Validate the top-level envelope exactly.** Exact nested-axis and entry validation does not make the projection exact-shape if the backend silently accepts unknown top-level keys. Define required and explicitly optional envelope keys, reject all others, and probe one unknown top-level key while every nested value is valid.
3. **Probe the rendered/aggregate result, not only helper predicates.** Construct a fully valid positive payload, mutate one trust-boundary field to a coercible wrong type, and print the final card/status/certification output. A success tone or completion claim is a material fail-open even when lower-level validators are strict.
4. **Check backend/client parity with the same counterexample classes.** At minimum cover unknown keys, truthy non-booleans, bool-as-int values, duplicate IDs, vacuous zero-required completion, contradictory implementation/delivery states, and positive certification without a receipt. Record each layer's decisive returned object.
5. **Tests do not outweigh a deterministic boundary counterexample.** If focused suites pass but a direct pinned-source probe produces a positive claim from malformed input, verdict is `BLOCK`; add the missing regression test in the subsequent fix slice.

## Reviewer isolation, index recovery, and sequential commits

A live/default index or a shared alternate index is coordination state, not a durable review artifact. Concurrent reviewers can accidentally copy, reset, refresh, or contaminate it even when their summaries claim that no index changed.

Use these additional controls:

1. Give every concurrent reviewer a unique source-index path. Never share one review index between reviewers, and never point a reviewer at the default index or the index intended for a later commit.
2. Build the source index from `HEAD`, stage only the exact reviewed paths, record scope/hash/modes/blobs, then freeze it. All materialization and tests must use a private byte-for-byte copy.
3. Do not run metadata-writing commands such as `git write-tree` against the frozen source index. `git write-tree` can rewrite its cache-tree extension and change the raw checksum while leaving scope, blobs, and cached diff unchanged.
4. Treat cached binary-diff hash + ordered scope + modes/blob IDs as semantic artifact identity. Treat the raw index checksum as an additional boundary-integrity signal. If a contract requires checksum stability, metadata-only checksum churn still blocks that review envelope and requires a fresh source index.
5. After all reviewers finish, reconstruct the commit index from `HEAD` and the reviewed paths; do not trust or reuse a reviewer-touched index. Recompute exact hash, scope, excluded paths, and blobs before commit.

If an index is contaminated or references blobs unavailable in the current repository:

- first print the ambient `GIT_INDEX_FILE`; in a persistent shell, an old export can make apparently default-index diagnostics read the wrong repository index;
- preserve the suspect index under `/tmp` for diagnosis;
- create a new index with `GIT_INDEX_FILE=<new> git read-tree HEAD`;
- stage only the known exact scope into the new index;
- verify cached diff hygiene, scope, exclusions, blobs, and expected hash;
- use the verified clean index without resetting or overwriting the worktree;
- when restoring the real default index, address the actual Git directory (`git rev-parse --git-dir`), then perform every readback with `env -u GIT_INDEX_FILE git ...`;
- explicitly verify current branch/HEAD, exact scoped status, excluded-path staged count, and total staged count; only then unset the persistent shell variable for subsequent commands.

Do not diagnose a default index as corrupt from commands that still inherit an alternate `GIT_INDEX_FILE`. Conversely, copying a clean file to `.git/index` is not verified recovery until the readback is run with the ambient alternate index removed.

For two disjoint reviewed commits in one repository, the second commit must be based on the first commit's new `HEAD`. Rebuild its index from that new `HEAD`, stage only the second reviewed scope, and prove equivalence with the exact scoped diff hash and reviewed path blob IDs. The full tree ID will legitimately differ from the pre-first-commit review tree because it now contains the first disjoint commit.

A reviewer statement that it did not modify the index is not sufficient evidence. Always perform fresh post-review scope/hash/blob readback before opening the commit gate.

### Async review-result triage

Background reviews can complete out of order long after newer artifacts supersede them. Before acting on any PASS or BLOCK:

1. Extract the review's exact hash, scope, and staged blob IDs before reading its recommendations as current work.
2. Compare them with the current candidate identity. If any differ, label the result `STALE_REVIEW`; retain its counterexample as historical evidence, but do not reopen or close the current gate from that verdict.
3. Check whether each stale counterexample is already covered by a later regression or pinned-byte review. Do not repeatedly patch the current artifact from findings against obsolete blobs without reproducing them on current bytes.
4. Keep the current gate closed until the latest identity has its own explicit stable PASS. A stale PASS cannot certify a successor, and a stale BLOCK cannot invalidate a successor merely because its message arrived later.
5. In user-facing status, lead with `reviewed_hash` versus `current_hash`; avoid replaying the full obsolete narrative unless it exposes an untested counterexample that still reproduces.

## Live multi-file SSOT reviews outside Git

Applicability: a read-only certification names several live source/config/test files, another process may repair them during review, and there is no immutable commit/index artifact to pin. Anti-condition: the requester explicitly wants the newest live state and can pause writers or provide an immutable snapshot; in that case certify the stable snapshot instead.

Treat the named files as one identity bundle rather than independent paths:

1. Hash every named source, config, registry, and test file before inspection; record ordered path + SHA-256.
2. Run focused tests and deterministic in-memory counterexamples with bytecode writes disabled (`python -B` or `PYTHONDONTWRITEBYTECODE=1`). Avoid `py_compile` in a no-modification review because it can refresh `__pycache__`; if syntax proof is needed, read and `compile(source, path, "exec")` in memory.
3. Re-hash the complete bundle after each long-running parallel test group. A source/config pair can drift between two otherwise green commands, so per-command hashes are not enough.
4. If any file changes, discard conclusions that depend on the old/new mixture, label the run `LIVE_BUNDLE_DRIFT`, reread the changed files, and rerun all material probes against one stable bundle. Do not merge an old source reading with a new registry test result.
5. Before verdict, re-hash the full bundle once more and print the reviewed/final bundle identities. If it is still moving, issue no certification vote beyond `amend/reject due to unstable artifact`.

For enforcement split across code and declarative configuration, probe the effective loaded state as well as file text. A mode such as `strict_active_tasks` can still evaluate false when a required root/allowlist key is absent. Print both the raw enforcement object and the effective predicate result.

For fail-closed intake or routing claims, do not stop at the canonical producer and autorun eligibility command. Probe every generic lifecycle boundary that can advance a pre-existing/directly-written record: aggregate `is_dispatchable`, manual claim/transition gate, scheduler selector, and worker bridge. The smallest decisive read-only counterexample is an in-memory missing/invalid envelope that reports whether each boundary accepts it. Green producer tests cannot outweigh a generic lifecycle bypass.

When a readiness report separates architecture/configuration/live queue, require non-vacuous negative evidence for the queue layer. `active=0, missing=[], invalid=[]` is an honest empty observation, not proof that a malformed active record is blocked. Test missing, invalid, conflicting, and valid active fixtures in an isolated root, and ensure top-level readiness does not call the architecture complete while an untested generic bypass remains.

## Closure check

Immediately before verdict, recompute scope, hash, and target blob IDs:

```text
reviewed_exact_hash: <initial hash>
final_live_hash: <fresh hash>
artifact_stable: true|false
```

PASS requires expected hash = reviewed hash, stable initial/final scope and blobs, claim-linked evidence from those pinned bytes, exact-source tests/probes, and no material finding. Otherwise BLOCK with the smallest deterministic reproduction. A concurrently fixed hash requires its own review; it cannot retroactively certify the blocked original.