# Canonical Content Hash Freshness at Closure

## Applicability

Use this checklist when a closeout claim relies on a derived search index, retrieval packet, evidence manifest, cache, or projection whose hash is supposed to bind back to a canonical source file.

Anti-conditions:

- Skip when the hash is only an opaque external identifier with no documented source-recomputation contract.
- Do not apply a Markdown block algorithm to databases, binary artifacts, signed payloads, or APIs; use their canonicalization contract instead.
- A fixture-only hash test does not prove a live index or runtime adapter is fresh.

## Required proof chain

1. Identify the canonical source and the exact identity tuple used by the producer, such as:
   - canonical relative path;
   - heading or record key;
   - line/record range;
   - normalized canonical content.
2. Recompute the digest from fresh source bytes using the producer's actual algorithm. Prefer importing/calling the producer implementation. If a boundary forces a mirror implementation, add a producer-parity test so algorithm drift fails visibly.
3. Compare every identity component, not only whether the supplied hash matches a hexadecimal regex.
4. Fail closed for:
   - missing source;
   - path traversal or source outside the canonical root;
   - malformed identity fields;
   - stale line/record ranges;
   - changed source content;
   - forged or missing digest.
5. Keep the verification projection authority-neutral. Return path/key, digest status, bounded counts, and typed errors; do not leak canonical body text, excerpts, secrets, or grant execution authority.
6. Distinguish verification levels explicitly:
   - injected/fixture contract check;
   - live adapter readback;
   - canonical source recomputation;
   - downstream consumer E2E.
   Passing one level does not imply the next.
7. After changing source notes or closure reports, refresh derived indexes and dashboards through their official generators, then rerun source recomputation and read back freshness metadata.

## TDD minimum

RED tests should independently prove:

- a correct live packet can be recomputed from a temporary canonical source;
- a forged or stale digest makes the gate fail;
- an out-of-root path is rejected;
- the runtime selfcheck exposes a dedicated freshness field and cannot PASS when it is false.

For a dependency-injected search seam, report canonical verification as `not_run`/`null` unless the injected fixture supplies a real canonical root and producer-compatible identity. Never label an injected adapter test as live disk verification.

## Closure reporting

A precise closeout statement is:

> Current live retrieval hits were recomputed from the canonical source and matched the producer identity contract.

It is not evidence that:

- every historical source record is semantically correct;
- every downstream runtime consumer uses those packets;
- an independent verifier approved the slice;
- the whole system is production-certified.

Record remaining boundaries separately in the Converge Matrix.
