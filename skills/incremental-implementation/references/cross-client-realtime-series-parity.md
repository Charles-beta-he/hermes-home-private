# Cross-client realtime-series parity slice

Scope: domain-level procedure for source-driven parity between two client implementations of realtime charts, order books, telemetry, or other keyed series.

Source boundary: distilled from a verified implementation session; examples are generic and contain no project paths, branches, ports, commit IDs, or product-specific fields.

Applicability:
- One client is an explicit behavioral reference.
- The target already receives equivalent anonymous/read-only data.
- The change is local merge logic without new APIs, credentials, remote writes, financial actions, or production changes.

Anti-conditions:
- Do not infer behavior from library capability alone.
- Do not invent unsupported periods, fields, or entry points.
- Do not treat pure-function tests as live-backend, device, or visual-parity evidence.

Falsifier: if the reference protocol intentionally delivers immutable, unique records and forbids same-key revisions, replacement/upsert behavior is not applicable; preserve append-only semantics instead.

## Procedure

1. Cite the reference implementation’s exact branch: same identity/time bucket means replace/update; a new identity/time bucket means append.
2. Inspect every target merge path. Initial snapshot-plus-stream reconciliation and incremental stream updates often duplicate subtly different logic; route both through one tested rule.
3. Write a behavioral RED before production code. Prefer a fixture that executes the old merge rule and proves a same-bucket update remains stale. A missing-module/import failure alone proves only that an extraction seam is absent, not that the product bug exists.
4. Extract the smallest pure helper:
   - derive identity with nullish fallback (`timestamp ?? time`), not truthy fallback;
   - normalize protocol-equivalent numeric/string keys with `String(value)`;
   - replace the matching record without growing the list;
   - append a genuinely new key;
   - process incoming batches sequentially;
   - define the missing-key policy explicitly, usually append rather than collapsing missing keys together.
5. GREEN assertions cover same-key replacement and stable length, new-key append, numeric/string normalization, batched replace-plus-append, and both initial/incremental consumer paths.
6. Run focused lint on helper and consumer, build/typecheck, and `git diff --check`. If the consumer has baseline lint errors, use blame evidence and label `BASELINE_ONLY_FAILURE`; never report a blanket PASS.
7. Commit only helper and consumer wiring. Read back clean status, log, and `git show --check`, then run the project certification loop.
8. Record boundaries: pure-function/build evidence supports a local verification level only; independent review or observed live same-key traffic is required for stronger claims, while device/full-parity claims remain separate.

## Async review hygiene

- Bind every verdict to immutable revisions and the reviewer’s actual dispatched scope.
- A late result for an older baseline certifies only that baseline and scope.
- If code advances during review, named ancestor revisions can still be reviewed, but newer follow-ups require their own scoped review.
- Keep local runtime processes alive only while a named verifier needs them; afterward terminate only owned exact processes and read back the relevant resources.
