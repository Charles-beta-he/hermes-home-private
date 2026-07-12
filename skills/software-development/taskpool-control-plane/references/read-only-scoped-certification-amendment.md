# Read-Only Scoped Certification Amendment Verification

## Applicability

Use this procedure when an existing taskpool/local-control-plane certification packet has a candidate verdict and the user requests a narrow, independent, read-only final verification. It is especially useful when evidence is hash-bound, negative parser cases must be reproduced, subprocess cleanup is material, and broader release/external/multimodel claims are explicitly excluded.

## Anti-conditions

Do not use this as authority to:

- mutate task, cron, scheduler, worker, adapter, or live lifecycle state;
- repair evidence in place or regenerate packet artifacts;
- call external services or open credentials/OAuth;
- upgrade a scoped local verdict into clean-release, historical-outcome, external-adapter, global-system, or real multi-model certification.

If required evidence is missing or mismatched, return `AMEND` or `REJECT`; do not silently broaden the investigation or manufacture replacement evidence.

## Procedure

1. **Freeze the requested check list and boundary.** Record the exact checks, prohibited actions, claimed verdict, explicit exclusions, and required final schema (`APPROVE`/`AMEND`/`REJECT`, `best_within_constraints`, unresolved High/Critical, and whether the exact candidate claim is supported).

2. **Run the hash manifest from its declared root.** Relative manifest entries are resolved against the current working directory. Determine the packet/repository root from the packet, spec, or project guidance, then execute the user's exact checksum command from that root. A failure caused only by running from the wrong directory is not artifact drift; rerun the exact command from the declared root and report the final grounded result. Do not rewrite the manifest.

3. **Inspect parser totality and tests before reproducing malformed cases.** Treat parsing as a typed result such as `(value, error)`; never turn a decode error into an empty list, ordinary string, zero budget, or legacy `SKIP`. Cover the entire input surface: non-object proof containers, wrong `files_changed` container type, non-string/empty entries, malformed or half-bracketed inline lists, non-string glob elements, invalid budgets, and valid legacy comma-separated compatibility. Record parse violations before any no-constraint skip path. Reproduce each requested malformed input independently in a self-cleaning temporary directory, assert the returned status is fail-closed, and also execute the focused regression tests. Prevent incidental bytecode/cache writes when practical (for example `PYTHONDONTWRITEBYTECODE=1`).

4. **Inspect and execute subprocess crash-release coverage.** Verify the implementation uses an OS-released ownership primitive (for example a held `flock` descriptor), keeps one stable lock inode (do not unlink on release), acquires the lock before source reads or projection/state writes, and serializes any fixed-name temporary-file/atomic-replace path under that same lock. The test must first prove contention, kill/crash the child, wait/reap it, reacquire the lock, release it, and have a `finally` cleanup path. Run the focused crash-release test, then perform a separate process-table readback using a narrowly identifying marker. Require zero residual matching children.

5. **Verify saved suite summaries as evidence, not fresh full-suite execution.** Read the saved output files, confirm their terminal summaries and exit semantics, and confirm the files are included in the passing hash manifest. Do not rerun broad suites unless explicitly requested.

6. **Enforce exact-version freeze.** Once the suite output and manifest are generated, freeze every hash-bound production file, test, Spec, packet, and runtime snapshot until the independent verdict returns. A reviewer PASS for `vN` cannot certify `vN+1`, even when later changes are only stricter tests or hardening. If any bound byte changes: rerun the affected focused tests, rerun the full claimed manifest, regenerate runtime snapshots when their freshness matters, emit a new manifest version, and request a new exact-version verifier vote. Timeout, missing summary, or an older-version PASS is not a vote for the current candidate.

7. **Inspect scope honesty and verdict prerequisites.** Compare packet exclusions, known nonclaims, acceptance criteria, and candidate verdict. A scoped local certification may be approved while historical outcomes, external adapters, production execution, clean release/install replay, and real multi-model quorum remain excluded, but only if those exclusions are explicit, fail-closed, and not used as supporting evidence.

8. **Issue the bounded verdict.**
   - `APPROVE`: all requested checks pass, hashes bind the reviewed evidence, and no unresolved High/Critical remains inside scope.
   - `AMEND`: evidence is repairable or incomplete without disproving the candidate, but the exact claim is not yet supported.
   - `REJECT`: a material invariant fails, evidence contradicts the packet, exclusions are dishonest, or a High/Critical remains unresolved.

9. **Land certification without circular evidence.** Keep the reviewed candidate packet immutable. Store the independent verdict as a separate receipt that names the candidate packet digest, manifest digest/path, reviewer identity/handle, exact scope, exclusions, and vote. The final SSOT may reference both immutable artifacts; if updating the SSOT changes a hash-bound Spec, create a closure/readback manifest rather than pretending the pre-update manifest covered the new bytes.

## Verification checklist

- [ ] Exact manifest command passed from the declared evidence root.
- [ ] Manifest, suite output, runtime snapshots, packet, Spec, source, and tests stayed byte-frozen through the exact-version verifier vote.
- [ ] Every requested malformed case independently returned `FAIL` with the expected explicit violation.
- [ ] Parser totality covered wrong top-level/container/entry types as well as malformed serialization, while valid legacy syntax remained supported.
- [ ] Matching focused parser tests passed.
- [ ] Crash-release test passed after source/test inspection, with lock ownership acquired before source/projection access and no lock-file unlink race.
- [ ] Separate post-test process readback found zero residual child.
- [ ] Saved full-suite summaries were read and hash-bound.
- [ ] Candidate verdict, exclusions, nonclaims, and independent-verifier criterion were compared.
- [ ] Final answer names unresolved High/Critical findings and states whether the exact scoped certification claim is supported.
- [ ] Final certification receipt references the immutable candidate/manifest instead of rewriting the reviewed packet.
- [ ] No live task/cron/external/credential/release mutation occurred.

## Pitfalls

- **Wrong-root false mismatch:** checksum manifests with relative paths are cwd-sensitive. Diagnose the declared root before treating `FAILED open or read` as evidence corruption.
- **Permissive parse fallback:** JSON/YAML/list decode failure must be an explicit violation, not a comma-split string, empty constraint, zero budget, or legacy skip. Validate top-level and element types too.
- **Post-review hardening drift:** a stricter patch after `APPROVE` still creates a new candidate. Regenerate evidence and obtain an exact-version vote; do not inherit the old PASS.
- **Lock-file TOCTOU:** existence checks and unlink-on-release can create two lock inodes. Hold the descriptor on one stable inode and serialize fixed temporary-state writes under it.
- **Test-name-as-proof:** inspect assertions and implementation; then independently reproduce the negative case.
- **Reaped-by-test assumption:** a passing crash test is stronger with a fresh, separate zero-residual process readback.
- **Summary-only trust:** saved test output is acceptable only when its artifact hash is bound by the verified manifest.
- **Scope inflation:** `FULL_LOCAL_*_SCOPED` does not imply historical truth, clean release, external adapters, production behavior, global Agent OS, or real multi-model quorum.
- **Packet mutation during verification:** independent read-only verification should return an external verdict; do not edit the pending packet merely to mark yourself as the verifier unless separately authorized.
