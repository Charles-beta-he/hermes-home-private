# Realtime Bucket Upsert Semantics

Use this pattern when a frontend merges snapshots and streaming updates for candles, telemetry windows, time-series bars, or any keyed realtime bucket.

## Core invariant

A realtime record belongs to a bucket identified by a normalized key:

```ts
const bucketKey = (item: Item) => {
  const raw = item.timestamp ?? item.time;
  return raw == null ? null : String(raw);
};
```

- Existing key: replace at the existing index.
- New key: append in incoming order.
- Missing/null key: append without treating all missing keys as one bucket.
- Batched repeated updates to one key: the last incoming record wins.
- Do not mutate input arrays.

This deliberately preserves source order. Do not sort merely because timestamps exist unless the domain contract explicitly requires chronological repair. Some reference implementations append newly observed buckets even when their timestamp appears older.

## One rule for every ingress path

Use the same helper for:

1. initial snapshot + buffered realtime merge;
2. later incremental stream updates;
3. reconnect/backfill merges;
4. cached hydration plus fresh data, when applicable.

A correct helper wired into only one path leaves split semantics and is not a complete fix.

## Verification matrix

Test the real helper and consumer wiring:

- same numeric key replaces without increasing length;
- numeric/string forms such as `200` and `"200"` coalesce;
- a new key appends;
- repeated same-key items in one batch leave the last item;
- missing/null keys append independently;
- existing order is preserved;
- source arrays remain unchanged;
- every intended ingress path imports/calls the helper.

For UI charting, distinguish evidence levels:

- pure-function tests prove merge semantics;
- source-to-sink checks prove wiring;
- browser/runtime tests prove chart consumption;
- real backend traffic proves payload compatibility.

Never promote pure local tests into claims about live WebSocket payloads, production ordering, or device rendering.

## Pitfalls

- Filtering out an already-seen timestamp freezes corrections to the active bucket.
- Raw identity comparison duplicates `200` and `"200"`.
- Using an empty-string fallback key causes all malformed records to overwrite one another.
- Sorting after every merge can silently diverge from an append/replace reference contract.
- Mutating the existing list can defeat React/store change detection.

## Anti-conditions

Do not use replace-in-place when the domain defines multiple events per timestamp, revision history must be retained, or a compound key is required. Establish the canonical key and ordering contract first.