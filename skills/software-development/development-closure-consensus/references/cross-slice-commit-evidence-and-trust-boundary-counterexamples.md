# Cross-Slice Commit Evidence and Trust-Boundary Counterexamples

## Applicability

Use for closure reviews spanning staged and unstaged slices, nested repositories/submodules, authority or evidence projections, or timeout-managed subprocess trees. Dirty worktrees are allowed; the requirement is evidence attributable to the exact slice under review.

## Staged-snapshot isolation

A green test run from a dirty worktree may execute unstaged implementation or test files. Treat that as cross-slice evidence contamination.

1. Read staged, unstaged, and untracked state separately in every repository.
2. Inspect test selectors and pre-commit hooks. If staged file A causes tests for unstaged file B to run, the result does not prove the staged snapshot.
3. Validate the index snapshot in an isolated checkout/worktree, or order dependent commits explicitly and rerun after each baseline change.
4. Re-read staged names after tests/builds; generated assets and lockfiles must stay unstaged unless intentionally scoped.
5. Identify each reviewed index snapshot with a binary-safe patch hash and recompute it after all tests/probes:

   ```bash
   git diff --cached --binary | shasum -a 256
   ```

6. Record which snapshot and files each command consumed; pass counts alone are insufficient. In multi-repository reviews, report one independently recomputed hash per repository and list unstaged neighboring files separately.
7. If the cached hash or staged file list changes during inspection, stop and return a fail-closed `ARTIFACT_DRIFT` verdict. Findings against the old snapshot may remain advisory, but neither old inspection nor tests certify the new index. Report both `reviewed_exact_hash` and `current_exact_hash`, plus changed index blob IDs, then freeze/restage and restart the full review rather than silently continuing on a moving artifact.
8. When tests execute working-tree paths, compare each reviewed file's worktree blob (`git hash-object <path>`) with its index blob (`git rev-parse :<path>`). A matching patch hash does not prove the test process loaded index content when staged and working-tree blobs differ.
9. Treat `GIT_INDEX_FILE` as scoped authority, not ambient shell state. Prefix every index-reading command explicitly, avoid exporting it into broad test processes, and run tests against an archived tree in a subprocess with `GIT_INDEX_FILE` removed from the environment. Record the alternate-index checksum before and after review in addition to the patch hash; any unexplained checksum or entry drift is a blocker even when file count is unchanged.

## Trust-boundary probes

Type/schema checks do not prove relational status, evidence identity, or authority semantics. Run deterministic counterexamples against the actual validator or renderer for:

- nonexistent, directory, symlink, wrong-scope, wrong-action, or mismatched-ID evidence/authority references;
- positive authority status backed by a self-authored regular JSON file in an arbitrary temporary directory;
- grants lacking a trusted authority store, immutable digest binding, issuer/audit metadata, validity interval covering execution, or exact action/target binding;
- `healthy` with active findings;
- failed status without a failure finding;
- fully connected with stale/missing evidence, incomplete inventory, or insufficient independent evidence;
- malformed nested counters (string, bool-as-int, negative value, wrong container) that crash instead of producing an `invalid_*` veto;
- aggregate counters that disagree with accepted entries or duplicate IDs;
- `can_claim_complete=true` while any required procedure is blocked, pending, stale, or failed;
- certification-positive claims without an independently verifiable certification receipt.

For file-backed evidence, `Path.exists()` is insufficient because directories pass. Require a non-symlink regular file **and non-symlink ancestry**; `not path.is_symlink() and path.is_file()` alone still accepts `symlinked-parent/regular-leaf`. Apply this rule consistently to stage, control-move, system-part, receipt, cleanup, and authority evidence. Add a digest when content identity or immutability matters, and compute the digest and parse JSON from the same byte snapshot.

For exact authority, a field-matching JSON document is not independent authorization when the receipt producer can create it. At minimum, load grants from a separately controlled/allowlisted authority store and bind the receipt to grant identity plus content digest, trusted issuer, exact action/target, execution-time validity, **and a unique execution/receipt identity**. Probe grant reuse explicitly: two receipts with different IDs but the same grant/evidence must not satisfy an independent-success or promotion threshold unless the grant contract deliberately authorizes multiple executions and carries a bounded, auditable use policy. If a self-authored temporary grant, an unbound reusable grant, or receipt-ID-only duplication can produce `fully_connected` or a certification candidate, block the slice.

At presentation boundaries, mirror the critical semantic implications instead of validating only nonnegative numbers. Invoke the actual UI/model helper with contradictory data and inspect its returned label/tone; a card showing `0 / 2` with authority-blocked work must never render success or healthy certification.

Show invalid input, validator result, and resulting projected/delivery/certification state. Distinguish lower-level overclaim from global certification: a safe global label does not repair an unsound procedure-level state. Green focused tests are necessary evidence but do not override an executable counterexample.

## Timeout/process ownership

Review inner-child and outer-runner timeouts independently. Outer process-group cleanup is not proof when an inner layer catches timeout and returns normally.

- launch owned trees in isolated groups/sessions;
- signal the whole owned group, not just the leader;
- call `wait()` after `kill()` to reap;
- use one monotonic absolute deadline across preflight/token snapshots, child startup, output reads, browser automation, screenshot subprocesses, TERM grace, SIGKILL escalation, reaping, and post-action readback;
- pass only the remaining budget to every nested operation—a per-call timeout started near the deadline can overrun the total contract;
- budget child timeout + grace + readback below parent timeout;
- perform bounded lock/port/process readback;
- test leader-exits/descendant-survives and SIGTERM-ignoring descendant behavior with a safe real local process, not only mocked `killpg` calls;
- inspect current residual processes before claiming no leak.

## Read-only and no-open claims

Trace the dependency implementation behind wrapper flags. A wrapper named `status-only`, `read_only`, or `--no-open` is not proof:

- store initialization may create directories or keychain entries, clear expired records, save storage, start watchers, or touch caches before the wrapper returns;
- a directly invoked library handler may open the browser even when the wrapper suppresses its own `open` call;
- asserting one lock file is unchanged does not prove zero mutation across credential stores, keychains, caches, or dependency-managed state.

Require negative evidence at the actual dependency boundary. If a truly read-only API does not exist, do not claim status-only zero mutation.

## Ambient authority and secret channels

Moving a secret off argv closes only one exposure channel. Review inherited environment, stdin/pipe payloads, descendant environments, stdout/stderr, exception text, logs, traces, screenshots, temporary files, and public JSON. When credentials can originate in environment variables, child spawn calls need an explicit sanitized `env`; tests should inspect it rather than asserting only that argv is clean.

For durable or automatic authorization, inherited environment must not reshape the granted action. Pin audited app/client identity, authorization domain, callback target, scopes, timeout, and entrypoint explicitly, and scrub corresponding variables. A grant bound to `oauth_recovery_only` is not exact authority if ambient values can silently change which app/domain/scopes the consent covers.

## Lock and path atomicity

Path-shape checks and PID probes are not enough for concurrent authority/lock code:

- stale-lock inspect-then-unlink is TOCTOU-prone; bind cleanup to the inspected inode/lease or use an atomic ownership protocol;
- PID liveness alone is not ownership because PID reuse can preserve a stale lock; add a nonce/start-time identity where available;
- release must not unlink a replacement lock acquired by another process;
- symlink-component checks followed by ordinary path reads are check-then-use; authority files should use descriptor-based no-follow opens, inode verification, and owner/mode checks where the threat model includes concurrent local mutation.

## Secret output

Prefer output allowlists over recursive denylist redaction. Probe exception text, stderr/stdout tails, auth URLs and query parameters, nested authorization/provider errors, and short secrets.

## Closure verdict

Return `BLOCKED` when invalid authority/evidence can reach a trusted or completion-like state, timeout cleanup can bypass descendant cleanup/reaping, or commit evidence is materially contaminated by unstaged cross-slice code. Passing tests remain positive evidence but do not override those blockers.