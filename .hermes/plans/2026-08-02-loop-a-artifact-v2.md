# Loop A Candidate Artifact V2 Plan

**Goal:** Replace runtime-created candidate directories with an atomically created, immutable regular-file artifact contract, closing P1-R5-001 without weakening the threat model.
**Status:** current_candidate_recertification_and_cutover_preauthorization
**Created:** 2026-08-02
**Updated:** 2026-08-02 (Grok-4.5 final P1 repair + exact Codex closure APPROVE)
**Baseline aggregate:** bf53966d136baf265445f3d81efb5a65ca5f2ff6eebbce9e1acb95573eb6013d
**Pre-remediation aggregate (FAIL review):** 513e43b6b9f2331475eb58e648a8621605dcc8d51859185070045299a1f5e819
Current local candidate-set aggregate: `ba5d3e8e46bd79cda11065ddbf6834246f94a924fe8c2e28b9c396d98f6dd68f`

## Spec Brief

- Goal: Loop A publishes one digest-bound candidate artifact via a creation syscall that atomically returns the owned FD; no runtime `mkdirat -> openat` candidate identity window.
- Non-goals: no promotion, active write, cron/runtime cutover, commit, push, deployment, privileged broker, or threat-model weakening.
- Source facts: v1 directory publication is HOLD on P1-R5-001; user selected architecture option 2 on 2026-08-02.
- Business rules:
  - Candidate generation edits only `SKILL.md`; supporting active files are not copied or mutated in Loop A.
  - Candidate root is a pre-existing, owner-checked, non-symlink directory opened through held dirfds. Loop A must not create directory ancestors at runtime.
  - Candidate artifact is one versioned canonical regular file containing candidate `SKILL.md` bytes plus run/skill/source/candidate digests and size.
  - File creation uses descriptor-relative `O_CREAT|O_EXCL|O_NOFOLLOW`; all writes/hash/readback use the returned FD.
  - Artifact becomes authoritative only after fd write, fsync, schema/readback/digest verification, and a typed success receipt.
  - Failure cleanup is identity-bound; unsafe cleanup leaves a typed residual and forces ERROR/rc2.
  - Flat artifact naming avoids per-run/per-skill directory creation.
- Negative cases:
  - missing/unprovisioned candidate root; symlink/foreign owner root; forced name collision; post-create pathname swap; write/fsync/readback failure; malformed artifact; source active late swap; receipt/path override.
  - no active bytes change; no directory candidate or runtime-created candidate ancestor.
- Evidence: strict RED→GREEN tests, py_compile, full focused suite, isolated subprocess smoke, six-file non-self-referential digest, independent current-digest review.

## Objective Model

- Success criteria: P1-R5-001 is structurally removed from the execution path; no current P0/P1; v2 artifact and receipt are digest-bound; active remains unchanged.
- Constraints: local reversible worktree writes only; preserve existing selector/receipt/ledger/noagent semantics.
- Current state (2026-08-02 local worktree): V2 flat artifact path implemented; directory publish APIs removed; local exact candidate set certified; commit/runtime/cutover closed.
- Chosen path: v2 flat regular-file artifact under a provisioned candidate root.
- Main risks: production root provisioning and runtime/cutover remain unverified; same-UID pathname replacement is represented as typed residual and never pathname-cleaned.
- Verification: exact hostile tests + independent Codex CLI digest-bound APPROVE on the current bytes.

## Loop Contract

- Max implementation/repair iterations: 4
- Repeated failure limit: 2 per root cause
- Writer: Grok-4.5 fallback (Claude weekly quota exhausted); no silent substitute
- Verifier: deterministic tests then independent Codex read-only review
- Authority: local worktree writes only
- Stop: current-digest PASS with P0/P1=0, hard blocker, writer unavailable, or external/privileged gate

## Steps

- [x] Freeze baseline, architecture decision, and acceptance contract.
- [x] Create successor V2 spec/ADR without mutating the approved v1 frozen spec — docs/private/dreaming-v2-artifact-spec-20260802.md.
- [x] RED: artifact contract, preprovisioned root, atomic FD creation, identity cleanup, no directory publication.
- [x] GREEN: implement minimal V2 artifact writer and migrate Loop A consumers/receipts.
- [x] Run focused and full deterministic verification plus isolated smoke.
- [x] Recompute exact six-file aggregate and run independent digest-bound security/spec review.
  - Current candidate-set aggregate:
    `ba5d3e8e46bd79cda11065ddbf6834246f94a924fe8c2e28b9c396d98f6dd68f`
- [x] Repair current-digest P0/P1 and repeat deterministic + independent verification.
- [x] Update certification packet and converge local candidate state; runtime/cutover remain closed.

## Implementation landed (local worktree only)

### Core (`scripts/hermes_dreaming.py`)
- `CandidateResult.candidate_artifact` replaces `candidate_dir` / `candidate_skill_md`.
- `build_candidate_artifact_filename` → `candidate-v2--<run_id>--<skill>--<nonce>.json`.
- `canonical_candidate_envelope_bytes` / `validate_candidate_envelope` (sorted-key compact JSON + digest coherence).
- `generate_candidate`: open pre-provisioned candidates root via dirfd chain; `openat(O_CREAT|O_EXCL|O_NOFOLLOW|O_RDWR, 0600)`; fd-only write/fsync/readback/schema; late active/root gates; identity-bound cleanup.
- Removed directory publish path: `_copy_tree_at`, `_atomic_publish_directory_noreplace_at`, `atomic_publish_directory_noreplace`, `_verify_candidate_readback`.
- Loop A does **not** create `state/dreaming/candidates` or per-run/per-skill directories.
- `REASON_CANDIDATE_ROOT_UNPROVISIONED` + write-block taxonomy updated.

### Tests / callers
- Directory security tests replaced with V2 equivalents (collision O_EXCL, pathname swap/competitor preserve, fd write/fsync leak close, envelope validate, late swap, root unprovisioned, etc.).
- Nightly docstring + seed fixtures provision candidates root.
- Noagent isolated subprocess smoke: real wrapper → typed receipt + flat artifact + active unchanged.

### Local verification evidence (2026-08-02)
- `python3 -m py_compile` on dreaming/nightly/noagent/test modules: PASS
- `PYTHONPATH=scripts python3 -m pytest scripts/test_hermes_dreaming.py scripts/test_hermes_evolution_store.py scripts/test_long_evolution_guard.py -q` → **168 passed**
- Isolated noagent subprocess smoke → rc=0, `candidate_generated=true`, flat `candidate-v2--...json`, active hash unchanged
- `git diff --check` → clean
- No commit / push / deploy / cron / live cutover performed

### Explicit non-claims
- Certification is local and exact-digest candidate-set only.
- Not committed or cut over.
- Not authorized for production runtime or cron.
- V1 frozen spec/manifest untouched.

## Decisions

- User selected architecture option 2: atomically created regular-file artifact contract.
- V1 frozen spec remains immutable; V2 is a successor contract.
- Loop A currently mutates only `SKILL.md`, so V2 carries candidate `SKILL.md` bytes and metadata rather than copying the entire active directory.

## Files Expected

- docs/private/dreaming-v2-artifact-spec-20260802.md
- docs/private/dreaming-loop-a-certification-hold-20260801.md
- scripts/hermes_dreaming.py
- scripts/test_hermes_dreaming.py
- scripts/autonomous-evolution-nightly.py
- scripts/autonomous_evolution_nightly_noagent.py
- scripts/test_hermes_evolution_store.py (only if receipt/ledger contract requires)

## Remaining before commit / runtime / cutover

1. Explicit human authority for commit, production root provisioning, and cutover.
2. Fresh committed/deployed-byte digest readback against the certified candidate set.
3. Runtime/cron/consumer verification under the separately authorized target.

## Canonical six-file non-self-referential candidate-set aggregate recipe

Identity is a SHA-256 over the following six relative paths (worktree root),
in **sorted UTF-8 path order**. For each path, append exactly:

```text
utf8(relative_path) + NUL + ascii_decimal(byte_length) + NUL + raw_file_bytes
```

Files:

1. `docs/private/dreaming-v2-artifact-spec-20260802.md`
2. `scripts/autonomous-evolution-nightly.py`
3. `scripts/autonomous_evolution_nightly_noagent.py`
4. `scripts/hermes_dreaming.py`
5. `scripts/test_hermes_dreaming.py`
6. `scripts/test_hermes_evolution_store.py`

Python equivalent:

```python
import hashlib
from pathlib import Path
paths = sorted([...six relative paths...])
h = hashlib.sha256()
for rel in paths:
    data = Path(rel).read_bytes()
    h.update(rel.encode("utf-8"))
    h.update(b"\x00")
    h.update(str(len(data)).encode("ascii"))
    h.update(b"\x00")
    h.update(data)
print(h.hexdigest())
```

Do **not** include v1 frozen spec/manifest in this V2 remediation aggregate.
V1 frozen artifacts remain immutable historical evidence.

The hold/certification document and this execution plan are evidence consumers outside
the exact candidate set. They may record the resulting digest, but must not be hashed
into that digest; doing so would create an unstable self-reference.

## Remediation closed locally (2026-08-02, Grok-4.5)

- P1-1: removed pathname unlink authority from candidate cleanup; post-create failures always residual + `candidate_cleanup_failed` / cleaned=false / ERROR/rc2; deterministic competitor race never unlinks.
- P1-2: `validate_receipt` strict semantic (types, stage inventory/order/uniqueness/reason consistency, generation success requires V2 artifact projection; reject state_advanced/promoted).
- P1-3: `returncode != 0` clears all authority/progress flags and nulls artifact projection.
- P1-4: `candidate_artifact` projection flows typed receipt → classify health → nightly ledger → noagent payload/ledger; failure/nonzero → null.
- P2: envelope negative matrix; root-missing whole Loop A zero-write fail-closed; removed `_open_dir_at` create/mkdir capability; real noagent happy + root-missing + malformed/nonzero negatives.
- Final P1-001/P1-002: identity-missing immediate post-create `fstat` failures and ordinary non-`OSError` post-create failures enter the typed never-unlink residual funnel; downstream ERROR/rc2/null authority; pre-create ordinary exceptions and `BaseException` remain uncaught.
- Prior exact Codex CLI code closure: APPROVE, P0=0, P1=0, P2=0, stable pre/post digest on `298d98fd4dabfd06e2787c210125476a72982b784f04c2fcb3a617e024f5f8ab`; current `ba5d3e8e...` successor differs only by removal of trailing blank EOF lines and is undergoing a fresh exact operational preflight.
- Explicit non-claims at this checkpoint: no commit/push/deploy/cron/live/cutover/runtime certification has yet executed.

## Exact authorized cutover tuple (2026-08-02)

- Authority: the user granted `全部授权` in the active session for this exact Loop A continuation.
- Candidate identity: `sha256:ba5d3e8e46bd79cda11065ddbf6834246f94a924fe8c2e28b9c396d98f6dd68f` using the canonical six-file recipe above.
- Exact commit set; no implicit `git add -A`:
  - `.hermes/plans/2026-08-02-loop-a-artifact-v2.md`
  - `docs/private/dreaming-loop-a-certification-hold-20260801.md`
  - `docs/private/dreaming-v1-freeze-manifest-20260801.json`
  - `docs/private/dreaming-v1-frozen-spec-20260801.md`
  - `docs/private/dreaming-v2-artifact-spec-20260802.md`
  - `scripts/autonomous-evolution-nightly.py`
  - `scripts/autonomous_evolution_nightly_noagent.py`
  - `scripts/hermes_dreaming.py`
  - `scripts/test_hermes_dreaming.py`
  - `scripts/test_hermes_evolution_store.py`
- Exact deployed scripts:
  - `scripts/autonomous-evolution-nightly.py`
  - `scripts/autonomous_evolution_nightly_noagent.py`
  - `scripts/hermes_dreaming.py`
- Runtime target: `/Users/charles/.hermes`; existing cron job `600370f80d83`, schedule `0 2 * * *` in scheduler timezone `Asia/Shanghai`, local/no-agent.
- Time fence: require at least 30 minutes until the scheduler-reported next fire and refuse installation inside the ±30-minute wall-clock window around 02:00 Asia/Shanghai. In one immediately-pre-mutate readback, require the exact cron tuple unchanged and enabled, `fire_claim=null`, no in-flight nightly/noagent process, candidate-root absence, and unchanged parent path identities. Any mismatch aborts before mutation. The scheduler configuration is not mutated and the scheduler is not manually fired during this cutover.
- Pre-image: write a timestamped rollback manifest and byte-for-byte copies of existing runtime scripts before install. Record path, SHA-256, owner, group, mode, symlink bit, existence, cron tuple, candidate-root existence, parent identities, and a canonical active-skill manifest.
- Binding and success cutover: reprove candidate digest → exact reviewed index → local commit tree/blob IDs. Extract only the three script blobs from that commit. Hold destination directory FDs opened with `O_DIRECTORY|O_NOFOLLOW`; create same-filesystem unique temp regular files with `O_CREAT|O_EXCL|O_NOFOLLOW`, mode 0644; write/fsync/fstat/hash; rename descriptor-relatively over each runtime script; fsync parent after each rename. This three-path runtime replacement is the entire success cutover. Retain the timestamped pre-image rollback bundle; no active skill path is in the mutate set. Verify all destination hashes, owners, modes, regular-file types, and commit-blob equality before execution.
- Provision: through held non-symlink parent FDs, create only `state/dreaming/candidates` with owner `charles:staff`, mode 0700; reject any pre-existing nonconforming entry.
- Smoke: perform in-memory `compile(source, path, "exec")` on the three deployed bytes. Then execute exactly once with argv `[/usr/bin/python3, /Users/charles/.hermes/scripts/autonomous_evolution_nightly_noagent.py]`, cwd `/Users/charles/.hermes/scripts`, stdin `DEVNULL`, stdout/stderr captured, timeout 330 seconds, environment inherited except `HOME=/Users/charles`, `HERMES_HOME=/Users/charles/.hermes`, `PYTHONDONTWRITEBYTECODE=1`, and a unique `HERMES_DREAMING_RECEIPT_PATH` under `/Users/charles/.hermes/state/dreaming/receipts/`. Do not invoke the cron scheduler. Require rc=0; strict typed receipt schema/run-id/stage validation; `status=OK`, `job_success=true`, `candidate_generated=true`, `state_advanced=false`, `promoted=false`; exactly one new root entry; basename `candidate-v2--*.json`; regular file, non-symlink, owner charles, mode 0600, single link; envelope schema `hermes.dreaming.candidate.v2`; and candidate path/hash/size agreement across receipt, envelope, generation stage, and FD-based readback. Any mismatch is failure and forbids push.
- Active-skill no-touch fence: `/Users/charles/.hermes/skills/**/SKILL.md` is explicitly outside the mutation set. Opening and closing manifests cover sorted relative path, regular-file type, owner/group/mode, byte length, and bytes; reject symlinks, unreadable entries, additions, deletions, metadata changes, or aggregate drift.
- Success readback: commit parent/tree/index identity, deployed blob hashes, parent identities, candidate root, smoke receipt/artifact, active-skill manifest equality, and field-for-field cron tuple equality to the pre-image with the same enabled job and scheduler-reported next run.
- Failure handling: do not unlink candidate artifacts. Quarantine targets are unique non-existing names under held same-filesystem parent FDs and are prechecked with `lstat`/`fstatat` semantics. Restore old runtime scripts from held rollback bytes with the same descriptor-relative atomic protocol; move a newly introduced deployed `hermes_dreaming.py` inode by descriptor-relative rename to the rollback bundle; atomically rename the whole cutover-created candidate root to `state/dreaming/candidates.quarantine-<timestamp>` if identity-matched; otherwise preserve it in place. Inventory all selector/log/receipt/ledger/candidate residuals with hashes and `action=KEEP`. Do not claim full state rollback.
- Push: separate post-green action only. A failed deployment leaves the commit local and unpushed; retry may use only the same verified commit blobs or an explicit new review. After all green evidence, freshly fetch/read the exact remote branch, inspect the exact commit range, and use a non-force exact refspec. No force and no push on any runtime/readback failure.
- Receipt bundle: pre-image manifest, authorization reference, candidate/staged/commit/deployed digests, tests, operational reviewer votes, smoke stdout/rc, typed receipt, candidate inventory, active-skill pre/post manifests, cron pre/post tuple, rollback/quarantine inventory, and push receipt.
