# Proof-check autorun debt classification

Applicability: `brain_task_orchestrator.py proof-check --json` reports `terminal invalid autorun proof hash debt`, especially after historical tasks accumulated `proof:sha256:*` evidence from more than one proof system.

Anti-conditions:
- Do not whitelist or delete genuine autorun proof debt without append-only proof-log readback.
- Do not weaken the `hermes-autorun review -> done` proof-hash requirement.
- Do not treat every `proof:sha256:*` evidence value as an autorun proof-log membership claim; other proof systems may use labeled hashes such as `proof:sha256:artifact_bundle=...`.

## Root-cause distinction

There are two different meanings that can look similar in task evidence:

1. **Autorun closeout proof**: task body contains a lifecycle line like `Lifecycle transition \`review\` -> \`done\` by \`hermes-autorun...\``. These done tasks must have `proof:<sha256:...>` evidence that is present in the append-only autorun proof log and passes chain verification.
2. **Non-autorun artifact hash label**: task was closed by a bounded non-autorun worker/human path, but evidence contains `proof:sha256:<label>=<hash>` or similar deterministic artifact labels. These should remain structured evidence, but should not be validated against the autorun append-only log.

The durable predicate should classify autorun context from the lifecycle/audit line, not from the existence of a `proof:sha256:` evidence prefix alone.

## Regression pattern

Add a test with a done task containing:

```yaml
evidence:
  - proof:sha256:artifact_bundle=deadbeef
  - command: deterministic closeout PASS
```

and body sections:

```md
## Proof Log
- non-autorun deterministic artifact bundle hash retained.

## Final Handoff
- closed by bounded non-autorun worker.
```

Expected result: `proof-check --json` returns `PASS` and does not emit `terminal invalid autorun proof hash debt`.

Keep the existing autorun tests too:
- `hermes-autorun` done without proof must fail.
- `hermes-autorun` done with a proof hash missing from the append-only log must fail.
- `hermes-autorun` done with a real append-only proof hash must pass.

## Exact candidate predicate

Do not send every string beginning with `proof:sha256:` to the autorun proof-log verifier. The autorun candidate predicate must accept only the exact event-reference shape:

```text
proof:sha256:<64 lowercase-or-uppercase hex characters>
```

Reject compound/labeled values such as `proof:sha256:artifact=x`, `proof:sha256:spec=...`, or other proof namespaces from autorun membership checks. Separately require an autorun-closed done task to contain at least one exact candidate; otherwise a pile of labeled hashes could accidentally satisfy the done gate.

Avoid `int(...)`/string coercion in adjacent canonical-proof fields: booleans and floats can coerce to integers. For line ranges, require a real non-bool `int`, `start >= 1`, and `end >= start`.

## Historical bare-hash recovery and truthful reclassification

A bare 64-hex value can be either a genuine autorun event hash or a historical artifact digest. Never eliminate the warning by guessing.

1. Preserve the strict autorun validator.
2. Extract artifact/file references from the same task frontmatter.
3. Recompute SHA-256 over current referenced bytes.
4. Reclassify only exact byte matches to an explicit namespace such as `proof:artifact-sha256:<hash>`.
5. Write a reversible manifest containing task path, source artifact path, artifact hash, and task before/after hashes.
6. If several evidence lines in one task are changed sequentially, manifest hashes form a chain: each record's `task_after_sha256` must equal the next record's `task_before_sha256`; only the final record should match current task bytes.
7. For unmatched hashes, broaden read-only recovery to bounded evidence/workflow/vault/temp roots and referenced-path Git history. If still unmatched, keep the warning OPEN; do not relabel it as resolved legacy debt.

This distinguishes debt removal from debt hiding. A lower warning count is valid only for format false positives or byte-proven artifact reclassification.

## Migration-script parsing pitfall

Legacy proof payloads may contain `=`, `:`, or other label syntax. A migration parser that captures only `[A-Za-z0-9_.-]+` truncates or misses the payload. Capture the complete non-empty value after the known prefix, then require an exact frontmatter occurrence before mutation. Deduplicate repeated task/proof warnings during apply, but fail closed when the exact reference is absent.

## Verification

- Run focused positive and negative proof-check classification tests.
- Keep tests for: autorun done without an exact candidate fails; missing-log exact candidate fails; real append-only candidate passes; labeled artifact hashes do not create autorun warnings.
- Run full `test_brain_task_orchestrator.py` when the predicate is shared.
- Verify every reclassification manifest as an ordered per-task hash chain and recompute every source artifact digest.
- Run live `proof-check --json` and compare warning count. A drop is acceptable only for proved false positives or exact byte matches; remaining source-loss debt must stay visible.
- Run taskpool `selfcheck`, Local Brain validate/exhaustive audit, and scoped diff/format checks after historical task edits.
