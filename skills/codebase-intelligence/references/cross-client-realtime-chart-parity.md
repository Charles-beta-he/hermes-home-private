# Cross-client realtime-chart parity: selecting the next safe slice

## Applicability

Use when one client (native/mobile/desktop) is the behavioral reference for another client and the task is to identify the **next** anonymous, local, reversible chart/detail parity slice rather than implement the whole backlog.

Anti-conditions:

- Do not use reference-client code as authority for backend semantics when labels, endpoints, and subscription channels disagree.
- Do not rank credentialed alerts, orders, transfers, device-native sharing, or production writes as anonymous/local slices.
- Do not treat a build or static source comparison as runtime parity proof.

## Procedure

1. **Pin the comparison baseline.** Verify the target commit, relevant-file hashes, branch, and working-tree state. Re-check status before reporting because concurrent build/watch processes may create unrelated drift.
2. **Inventory visible behavior from the reference.** Trace controls, persisted state, HTTP initialization, realtime subscriptions, merge/update behavior, and navigation effects. Distinguish visible behavior from hidden implementation mechanics.
3. **Trace the target end to end.** Map control state -> request key -> HTTP response -> WS key/filter -> merge/process function -> chart update call. A UI control inventory alone misses data-contract defects.
4. **Model stream semantics explicitly.** For bucketed chart data, compare:
   - same bucket/key -> replace/upsert;
   - new bucket/key -> append;
   - stale/out-of-scope subscription -> reject.
   A generic timestamp de-duplicator is often wrong because it drops corrections to the current candle/bar.
5. **Normalize identity before comparison.** If timestamps can be strings or numbers, normalize them (for example `String(time ?? timestamp)`) before matching. Preserve pair/period/source identity in cache and subscription keys.
6. **Rank candidates by objective cost.** Prefer, in order:
   - correctness defects in an already-wired anonymous data path;
   - local preference/state parity with validated fallback;
   - display gaps backed by already-returned fields;
   - new source modes/endpoints only after anonymous capability probes resolve semantics.
7. **Separate safe candidates from gated differences.** For each candidate state source evidence, target evidence, prerequisites, risk, and the smallest RED -> GREEN proof. Put ambiguous API semantics, credentials, external effects, and device-only behavior in a gated section instead of silently copying them.

## Realtime candle/bar RED -> GREEN matrix

Given previous data ending in bucket `200`:

| Incoming data | RED symptom | GREEN requirement |
|---|---|---|
| bucket `200`, changed OHLCV | update is filtered as duplicate | length unchanged; bucket `200` replaced |
| bucket `300` | may append correctly | length +1; bucket `300` appended |
| existing `"200"`, incoming `200` | duplicate or missed update from type mismatch | normalized identity treats them as one bucket |
| old pair/period event | stale data contaminates current chart | event rejected by active identity/filter |

Prefer extracting the merge/upsert rule into a pure helper so these cases can be verified independently, then add build and anonymous runtime evidence that the current candle changes without duplicate bars.

## Candidate-report format

```text
Recommended next slice: <one bounded behavior>
Why now: <correctness/value vs cost>
Reference evidence: <file:symbol/line>
Target gap: <file:symbol/line>
Prerequisites: <existing API/WS/storage; no credentials>
Risk: <low/medium + concrete edge cases>
RED -> GREEN: <minimal deterministic case + runtime check>

Other safe candidates: ...
Gated/excluded differences: ...
Working-tree boundary: <relevant files unchanged; unrelated concurrent drift if any>
```

## Pitfalls

- **UI-first ranking:** choosing a visible accessory while the current realtime candle is frozen.
- **Deduplication-as-correctness:** filtering equal timestamps instead of upserting the current bucket.
- **Name-based API inference:** assuming `index`, `mark`, and `last` endpoint/channel names have consistent semantics without response probes.
- **Persistence without validation:** loading arbitrary storage values instead of whitelisting supported periods and falling back safely.
- **Concurrent-drift misattribution:** claiming the tree stayed clean after a watcher generated files; re-read status and bound ownership of unrelated changes.
