# Incremental list sync ordering

Scope: frontend stores that maintain a visible list via incremental sync, SSE invalidation, polling, push notifications, or cursor/outbox events. Especially applies when backend cursor order is optimized for correctness (`event_seq ASC`, append-only log order, pagination cursor order) but UI order is a product invariant (`latest first`, priority rank, business timestamp desc).

Anti-conditions: do not use this to override a backend/API contract that explicitly returns a ranked display list and documents that clients must preserve order; do not sort money/ledger rows by a different timestamp than the product surface specifies.

## Failure pattern

A common bug shape:

1. Initial/full list endpoint returns rows in correct display order, e.g. `createdAt DESC`.
2. Incremental endpoint returns changed events in cursor order, e.g. `event_seq ASC` so the client can advance the cursor safely.
3. Frontend store merges with `merged = [...incoming, ...existingWithoutDuplicates]`.
4. If `incoming` contains multiple newly created rows, the newest row within that batch is not first; it can appear in the middle of the visible list.
5. Later single-row pushes look normal, masking the bug until a batch, reconnect, visibility refresh, or accumulated event sync occurs.

## Debugging checklist

- Prove all navigation entries reach the same list surface before blaming UI routes.
- Trace every data source for the list: full fetch, incremental sync, single-item fetch, optimistic append/replace, persisted cache hydration.
- Compare backend order contracts separately:
  - full/list display order;
  - incremental cursor/event order;
  - changed-id lookup order after `findAllById`/repository retrieval;
  - deleted/read-all full-refresh branches.
- Check whether the page component renders store order directly or applies a selector/view-model sort.
- Create a minimal reproduction with at least three incoming changed items: `new-1`, `new-2`, `new-3-latest`; assert `new-3-latest` appears first after merge.

## Fix pattern

Prefer a store-level selector/helper that normalizes the page view model after every mutation path:

- preserve a stable display timestamp field from the backend (for notifications this is often `createdAt` delivery time; `occurredAt` may be business-event time and can be older);
- after merge/append/replace, dedupe by id and sort by the product display invariant;
- apply the same helper to full fetch, incremental sync, single-item fetch, and optimistic paths;
- keep cursor advancement separate from display order.

Example shape:

```ts
function notificationSortKey(n: Notification): number {
  const primary = Date.parse(n.createdAt ?? '') || 0;
  const secondary = Date.parse(n.occurredAt ?? '') || 0;
  return primary || secondary;
}

function orderNotifications(items: Notification[]): Notification[] {
  return [...items].sort((a, b) => notificationSortKey(b) - notificationSortKey(a));
}
```

If the type currently drops the display timestamp, fix normalization/type coverage first; otherwise the store cannot enforce the invariant.

## Regression tests

Add tests at the store boundary, not only service normalization:

- existing list already sorted;
- incremental sync returns multiple new items in cursor ASC order;
- merged list is still display-order DESC;
- fetchOne append/replace and full fetch use the same ordering helper;
- single-item sync still passes to avoid overfitting to batches.

## Session-derived example

A UVISA notification-center task showed this exact shape: `/notifications/sync?afterSeq>0` returned `notification_event_log` rows ordered by `event_seq ASC`, while the frontend store prepended `incoming` without sorting. Batch incremental sync could produce `new-1, new-2, new-3-latest, old-top`, so the latest message appeared in the middle. The two visible entry points both routed to `/notifications`; the root cause was merge ordering, not route/UI differences.
