# Notification Sync Time Semantics and Lifecycle Pause/Resume

Use when debugging or changing mobile/PWA notification centers that combine incremental sync, read-state updates, service-worker/client updates, and foreground/background lifecycle behavior.

## Problem pattern

A notification center may appear to reorder old messages after a read/update event:

```text
markRead / status update
-> backend emits mutation event
-> incremental sync returns the changed existing notification
-> frontend prepends every incoming item
-> old notification jumps to top
```

This is not a visual sorting bug in the card component; it is usually a merge-policy bug in the store/sync layer.

## Merge policy

For incremental notification sync:

- **New id**: may be inserted at the top, or placed according to the authoritative sort key.
- **Existing id**: replace/update in place; do not move solely because it was returned by a read/status mutation.
- **Deleted id**: remove from the current list.
- Avoid treating all `incoming` items as new.

If the backend contract distinguishes created vs updated vs deleted items, use that. If not, compare incoming IDs with the current list.

## Time semantics

Keep display and business times separate:

- `createdAt` / delivery time / notification inserted-at time:
  - card footer display time;
  - primary list sort key for “latest message in message center”.
- `occurredAt` / embedded business time:
  - event detail/audit text, e.g. protection start time, order event time, business transition time;
  - optional tie-breaker only when product/back-end contract says so.

Do **not** sort by the formatted card text string. Sort by raw timestamps.

Do **not** use a business event time embedded in body text as the notification list’s primary sort key. Backfilled or delayed business events can otherwise jump ahead of newly delivered notifications.

## Lifecycle coordination

When adding app foreground/background logic:

- Hidden/background/offline:
  - stop notification polling;
  - disconnect SSE/WebSocket or stop reconnect loops;
  - optionally send best-effort background heartbeat if the backend supports it.
- Foreground/online:
  - REST sync first to compensate missed events;
  - then reconnect SSE/WebSocket;
  - then resume polling.

Feature-flag new heartbeat endpoints if the backend is not deployed yet. Default off is safer than calling a missing endpoint.

## Authenticated activity offset

If normal authenticated business requests can offset explicit heartbeat:

- emit only minimal activity detail such as `{ at }`; do not broadcast URL/method/query globally;
- exclude heartbeat endpoints from activity offset so heartbeat does not suppress itself;
- debounce/in-flight guard resume events triggered by `visibilitychange`, `focus`, `pageshow`, and `online`;
- add disposed/cleanup guards so in-flight requests cannot recreate timers after logout/unmount.

## Verification checklist

- Existing read/status-updated notification keeps its previous index after sync.
- New notification still appears according to the intended “latest delivered” ordering.
- Deleted notification is removed.
- Card footer uses `createdAt` when available; business detail time remains available as `occurredAt`.
- Hidden/offline stops polling and realtime connection.
- Foreground/online does REST sync before realtime reconnect.
- Heartbeat is default-off or backend-compatible.
- Timer cleanup prevents post-unmount reschedule.
