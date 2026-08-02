# Dreaming Loop A Certification Hold — 2026-08-01

## Status

- Verdict: **LOCAL V2 CANDIDATE PASS** on the exact six-file digest below; cutover is human-authorized but remains execution/readback gated
- Independent review: Codex CLI 0.146.0 (`openai/gpt-5.6-sol`, read-only, session `019fc1df-ca18-76f1-ad31-76bec951dff6`) returned **APPROVE**
- Current findings: P0=0, P1=0, P2=0
- Promotion: still unavailable in Loop A; candidate-only runtime cutover: authorized, not yet executed at this checkpoint
- Base HEAD: `9e22bade18f29f6699af5d240a4436c388f59e6a`
- Seven-file reviewed aggregate (Round 5): `40097bf4c22aea3ad474bf2481adf50664c9cacfa52d8e18bd0f9dc1cb1b4777`
- Architecture decision (2026-08-02, human): option **3 / architecture 2** — amend candidate artifact to atomically created regular-file bundle (V2)

## Completed evidence (v1 + hold history)

- Candidate-only generation; active bytes unchanged.
- No promotion or state advancement in Loop A.
- Ownership, root-EUID, path escape, and symlink checks fail closed.
- Descriptor-relative publish/readback with `O_NOFOLLOW`, `fstat`, inode checks, and fd hashing.
- Digest-bound evaluator input; no post-gate candidate/active pathname content reads.
- Typed receipt handling; cleanup failure yields `job_success=false`, `ERROR`, and wrapper rc=2.
- Unsafe pathname cleanup and `shutil.rmtree` dead implementation removed.
- Round 5 review hashes were stable and review made no worktree mutation.
- Live script remained distinct and untouched; no matching cron, launchctl job, or process was found.

## Remaining P1 (historical): P1-R5-001

The temporary candidate directory is created by `mkdirat` and then opened by a separate `openat`. Under an active same-UID adversary, the directory entry can be replaced between those calls. The process cannot prove that the directory opened after the gap is the inode created by its preceding `mkdirat`.

Independent deterministic reproduction showed that a replacement directory could be opened, modified, and published with a typed `candidate_generated` result. An injected first-open failure also left an unparked `.tmp-candidate-*` because no creation-bound inode identity was available.

## Platform primitive audit

Fresh macOS SDK/manpage inspection confirmed:

- `mkdirat(2)` returns only success/failure, not an fd for the created directory.
- `mkdtempat_np(3)` returns the generated pathname, not an fd.
- `openat(2)` can bind an existing directory with `O_DIRECTORY|O_NOFOLLOW`, but remains a later syscall.
- `clonefileat(2)` / `fclonefileat(2)` atomically create destination objects and reject an existing destination, but do not return an fd for the destination; a later destination open retains the same replacement window.
- `renameatx_np(RENAME_EXCL)` safely publishes an already-bound source inode but cannot retroactively bind the inode created by `mkdirat`.

No pure unprivileged Darwin/POSIX primitive found in the inspected APIs atomically creates a directory and returns its fd. Closing this finding while retaining an actively malicious same-UID threat model therefore requires an isolation boundary (for example a separately owned broker) or a changed artifact representation that can use atomic regular-file creation.

## Human authority decision (recorded)

On 2026-08-02 the user selected architecture option 2 / decision 3:

> Amend the candidate artifact contract to an atomically created regular-file bundle (V2).

V1 frozen spec/manifest remain immutable. V2 is a successor contract under `docs/private/dreaming-v2-artifact-spec-20260802.md`.

## Local V2 implementation and candidate certification (worktree only)

Implemented in `/Users/charles/.hermes/worktrees/dreaming-loop-20260801` without commit/push/deploy/cron/live:

- Flat regular-file artifact via `openat(O_CREAT|O_EXCL|O_NOFOLLOW|O_RDWR, 0600)`.
- Canonical envelope (`hermes.dreaming.candidate.v2`) with run_id/skill/source_sha256/candidate_bytes_b64/candidate_sha256/size.
- Pre-provisioned candidates root only; Loop A does not create `state/dreaming/candidates` or run/skill directories.
- `CandidateResult.candidate_artifact`; directory publish APIs removed from execution path.
- Identity-bound cleanup; competitor pathname swap never unlinked; typed residual / cleanup_failed → job_success=false / ERROR / rc2 retained.
- Directory-oriented tests replaced by V2 security equivalents.

### Local verification

- py_compile PASS
- pytest focused three-file suite: **168 passed**
  (`test_hermes_dreaming.py` + `test_hermes_evolution_store.py` + `test_long_evolution_guard.py`)
- isolated noagent subprocess smoke PASS (flat artifact + active hash unchanged)
- git diff --check PASS

### Still required before commit, provisioning, or cutover

1. Exact human authority for commit, production candidate-root provisioning, and cutover.
2. Fresh post-action readback proving the committed/deployed bytes match the certified candidate digest.
3. Runtime/cron/consumer verification, which is outside this local candidate certification.

Until those complete: **CUTOVER HOLD remains**. The local six-file candidate set is
certified only at the exact digest below; it is not committed, deployed, activated, or
runtime-certified.

## Rollback

All implementation changes remain in `/Users/charles/.hermes/worktrees/dreaming-loop-20260801`. Nothing has been committed, pushed, deployed, or activated. The entire worktree can be discarded to return to base HEAD `9e22bade18f29f6699af5d240a4436c388f59e6a`.

## Resume verification

After exact authority for commit / provisioning / cutover:

- recompute the current six-file non-self-referential candidate-set aggregate on the V2 tree;
- run py_compile and the complete focused/guard suite;
- run isolated normal and blocked subprocess flows;
- prove live/active bytes unchanged;
- retain the current independent digest-bound review receipt;
- require P0=0, P1=0, and stable before/after hashes before runtime advancement.

## V2 remediation and certification note (2026-08-02, local candidate only)

Independent digest-bound review on aggregate
`513e43b6b9f2331475eb58e648a8621605dcc8d51859185070045299a1f5e819` reported
**FAIL** (P1×4, P2×1). Local remediation applied in this worktree only.

### Canonical six-file candidate-set aggregate recipe

SHA-256 over these six relative paths in **sorted UTF-8 path order**. For each
path append:

`utf8(relative_path) + NUL + ascii_decimal(byte_length) + NUL + raw_file_bytes`

1. `docs/private/dreaming-v2-artifact-spec-20260802.md`
2. `scripts/autonomous-evolution-nightly.py`
3. `scripts/autonomous_evolution_nightly_noagent.py`
4. `scripts/hermes_dreaming.py`
5. `scripts/test_hermes_dreaming.py`
6. `scripts/test_hermes_evolution_store.py`

This hold/certification document is deliberately outside the candidate set. Including a
document that embeds the candidate digest in the same digest creates an unstable
self-reference and cannot produce a truthful fixed identity. The execution plan is also
outside the candidate set. Both may bind the candidate digest, but neither contributes
bytes to it.

Current local candidate-set aggregate: `ba5d3e8e46bd79cda11065ddbf6834246f94a924fe8c2e28b9c396d98f6dd68f`. V1 frozen
spec/manifest are **not** part of this V2 aggregate and remain immutable.

### Remediation claims (local evidence only)

- P1-1 closed: no candidate pathname unlink on failure path; residual forced.
- P1-2 closed: strict semantic `validate_receipt` + V2 artifact projection binding.
- P1-3 closed: nonzero rc clears authority/progress flags + null projection.
- P1-4 closed: artifact projection through receipt/classify/nightly/noagent.
- P2 closed: envelope negatives, root-missing zero-write, no dir create helper.

### Final independent closure review (2026-08-02)

- Exact Codex CLI provenance: CLI `0.146.0`, model `gpt-5.6-sol`, provider `openai`,
  read-only sandbox, session `019fc1df-ca18-76f1-ad31-76bec951dff6`.
- The preceding exact review of digest
  `24a7ae94b4685fd027c4de142bbf92476876848d020b1bd82e28399a75f4d115`
  returned **AMEND** with P1×2: immediate post-create `fstat(fd)` failure was
  falsely reported cleaned when identity was unavailable, and ordinary non-`OSError`
  post-create exceptions escaped the typed residual funnel.
- Grok-4.5 repaired only `scripts/hermes_dreaming.py` and
  `scripts/test_hermes_dreaming.py` under strict RED→GREEN. Main-session verification
  as user `charles`: focused new regressions **9 passed**, full three-file suite
  **168 passed**, py_compile PASS, `git diff --check` clean.
- Final Codex closure review recomputed the current digest before and after, replayed
  both original counterexamples, audited unlink reachability, checked pre-create
  `RuntimeError` plus `KeyboardInterrupt`/`SystemExit` propagation, and verified
  run→nightly→noagent ERROR/rc2/null-authority projection.
- Final verdict on
  `298d98fd4dabfd06e2787c210125476a72982b784f04c2fcb3a617e024f5f8ab`:
  **APPROVE; P0=0, P1=0, P2=0; pre/post digest identical**.
- Reviewer limitation: the strict read-only sandbox had no writable temporary
  directory, so its filesystem-dependent pytest suite could not run. This is covered
  by the fresh main-session `charles` run above, not counted as a reviewer pass.

**Local six-file V2 candidate: CERTIFIED at the exact digest above. The user subsequently
granted `全部授权`; commit, provisioning, candidate-only deployment and cutover are now
preauthorized but remain subject to the amended operational preflight and fresh readback.
Loop A still has no active-skill promotion authority.**
