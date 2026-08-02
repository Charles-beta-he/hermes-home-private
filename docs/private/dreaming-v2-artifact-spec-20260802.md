# Hermes Dreaming Candidate Artifact V2 — Successor Contract

status: APPROVED_ARCHITECTURE / IMPLEMENTATION_PENDING
approved_by: user
approved_at_local: 2026-08-02
supersedes_candidate_representation_only: docs/private/dreaming-v1-frozen-spec-20260801.md
baseline_seven_file_aggregate: bf53966d136baf265445f3d81efb5a65ca5f2ff6eebbce9e1acb95573eb6013d
risk_class: local_reversible

## Decision

The user selected architecture option 2: replace runtime-created directory candidates with an atomically created regular-file artifact contract. The approved V1 control-loop invariants remain authoritative except where this document explicitly replaces the candidate representation and publication protocol.

## Goal

Close P1-R5-001 by removing every runtime `mkdirat -> openat` candidate-identity transition from Loop A. Candidate generation publishes one immutable, digest-bound regular file through a syscall that atomically creates the file and returns its owned descriptor.

## Non-goals and closed authority

- No active-skill mutation or promotion.
- No runtime/cron cutover, deployment, commit, or push.
- No privileged helper or staging broker.
- No weakening of the active same-UID namespace adversary model for the scoped creation-identity claim.
- No full skill-directory snapshot. Loop A V2 changes only `SKILL.md`; support files remain active-tree inputs and are not copied into the candidate.

## Provisioned root contract

1. `HERMES_HOME/state/dreaming/candidates` is a pre-existing provisioned directory.
2. Loop A must not create `state`, `dreaming`, `candidates`, run, skill, temporary-directory, cleanup-directory, or shard directories.
3. Missing root returns typed `candidate_root_unprovisioned`, with zero candidate/state ancestor creation by the generation stage.
4. Each existing component is opened descriptor-relatively with `O_DIRECTORY|O_NOFOLLOW` and checked by `fstat` for directory type and expected owner.
5. Writes are anchored to the held candidates-root FD. Pathname readback cannot substitute for descriptor identity.

Provisioning is outside Loop A and remains a foreground/operator-controlled concern. This contract does not authorize a new provisioner or runtime cutover.

## Artifact layout

Artifacts are flat children of the provisioned candidates root. No run or skill directory is created.

Safe filename shape:

```text
candidate-v2--<safe-run-token>--<safe-skill-token>--<nonce>.json
```

Requirements:

- one path component only;
- no slash, backslash, dot-segment, NUL, normalization ambiguity, or caller-supplied pathname;
- bounded length;
- collision handled by `O_EXCL`, never overwrite/retry onto an existing name;
- nonce source is injectable for deterministic collision tests.

## Atomic creation protocol

The writer must use descriptor-relative creation equivalent to:

```text
openat(candidates_root_fd, name,
       O_CREAT | O_EXCL | O_NOFOLLOW | O_RDWR,
       0600)
```

The returned FD is the creation identity. The implementation must not create a pathname and then reopen it to establish ownership.

All operations before success use that FD:

1. build canonical envelope bytes in memory;
2. write all bytes to the returned FD;
3. `fsync(fd)`;
4. seek/read the same FD;
5. validate exact bytes, schema, semantic bindings, size, and digests;
6. compare `fstat(fd)` with `lstat(name, dir_fd=root_fd)` immediately before success;
7. emit a typed receipt bound to artifact filename, inode identity, envelope digest, source digest, and candidate digest.

No pathname content read is authoritative.

## Canonical envelope V2

Canonical encoding is UTF-8 JSON with sorted keys, compact separators, no NaN, and a trailing newline policy fixed by implementation/tests. The exact top-level key inventory is versioned and strict:

```json
{
  "candidate_bytes_b64": "...",
  "candidate_sha256": "64 lowercase hex",
  "candidate_size": 0,
  "run_id": "semantic run id",
  "schema_version": "hermes.dreaming.candidate.v2",
  "skill_name": "semantic skill name",
  "source_sha256": "64 lowercase hex"
}
```

Validation requirements:

- exact key set; no missing or unknown keys;
- exact primitive types;
- strict Base64 decode;
- decoded length equals `candidate_size`;
- decoded SHA-256 equals `candidate_sha256`;
- source digest equals the verified active `SKILL.md` FD digest used for generation;
- run and skill identities exactly equal the invocation identities;
- envelope bytes re-canonicalize byte-for-byte;
- candidate bytes decode as UTF-8 before evaluator use.

The receipt additionally carries the envelope SHA-256 and `(st_dev, st_ino)` of the created file.

## Failure and residual protocol

1. Before artifact creation, failures leave zero artifact residue.
2. After successful `O_EXCL` creation, Loop A must **never unlink the artifact pathname on a failure path** under the active same-UID namespace-adversary model. `lstat(name) -> unlink(name)` is not a conditional unlink primitive: an adversary can replace the entry between the two syscalls and cause deletion of a competitor.
3. The creation FD and its `(st_dev, st_ino)` identify the owned artifact only for evidence. Closing the FD does not authorize pathname deletion.
4. A collision never opens, changes, or deletes the existing entry.
5. Every post-create failure therefore preserves the owned or unclassified residual and yields:
   - generation reason `candidate_cleanup_failed`;
   - `candidate_cleaned=false`;
   - typed `residual_reason` and creation-bound identity;
   - `job_success=false`;
   - `write_blocked=true`;
   - `degraded=true`;
   - classification `ERROR`;
   - nightly/no-agent rc `2`.
6. No later pathname observation may upgrade the residual to cleaned. Automated conditional deletion requires a separately authorized broker/platform primitive and is outside architecture 2.
7. A residual receipt must distinguish creation-owned identity, collision/competitor-preserved, and pre-create absence without claiming unsafe cleanup success.

## Result and receipt migration

V2 uses `candidate_artifact` rather than `candidate_dir` / `candidate_skill_md` as the authoritative location. `candidate_content` remains digest-bound bytes decoded from the held artifact FD.

Required success details:

- `candidate_artifact`;
- `artifact_schema_version`;
- `artifact_sha256`;
- `artifact_size`;
- `artifact_st_dev` / `artifact_st_ino`;
- `source_sha256`;
- `candidate_sha256` / `candidate_size`;
- `run_id` / `skill_name`;
- applied/unsupported findings.

Directory candidate fields must not retain hidden authority. Compatibility projection, if temporarily retained, must be explicitly null/deprecated and must not trigger pathname reads.

## Acceptance matrix

| Claim | Required evidence |
|---|---|
| no mkdir/open creation window | production call-path audit; deterministic test that no candidate-directory creation helper executes |
| root is provisioned | missing-root test: typed failure, no ancestor creation |
| atomic creation identity | forced name collision sentinel; returned-FD identity assertions |
| canonical artifact | repeated-build byte equality; exact schema and malformed/unknown/type/Base64/digest negatives |
| active unchanged | active bytes/hash before and after normal and hostile flows |
| no directory candidate | root inventory contains regular artifact only |
| pathname swap fails closed | deterministic post-create replacement probe; outside/competitor bytes unchanged |
| cleanup is identity-bound | competitor-preservation and typed residual/rc2 tests |
| receipt/ledger/no-agent migrate | exact structured success/error tests; legacy stdout cannot upgrade |
| evaluator is digest-bound | post-return pathname swap does not change evaluator input |
| no regression | focused/full pytest, py_compile, isolated subprocess smoke, git diff check |
| certification | stable opening/closing aggregate and independent current-digest review with P0=0/P1=0 |

## Rollback

All V2 work remains local to `/Users/charles/.hermes/worktrees/dreaming-loop-20260801`. Before runtime cutover, rollback is discarding the local worktree changes. V1 remains frozen historical architecture evidence and is not edited by this successor.

## Converge rule

Architecture approval is not implementation certification. Loop A remains HOLD until current V2 bytes pass every acceptance row, closing aggregate is stable, independent review reports no P0/P1, and no current-digest review remains pending. Runtime, promotion, cron, and active writes remain blocked.
