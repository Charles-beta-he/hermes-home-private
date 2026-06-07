---
name: concurrent-async-guard
category: software-development
description: "Use when skip-and-resync dirty-bit pattern for Zustand (or similar) stores with one-at-a-time async guards. Prevents rapid-fire triggers (SSE, polling, visibility) from being silently dropped. Uses atomic set() updater to close race windows. Use when syncInFlight guard causes missed events, or when concurrent async calls need eventual consistency without unbounded recursion."
tags: [zustand, concurrency, state-management, async, guard, sse, realtime]
triggers:
  - syncInFlight guard skipping events
  - concurrent async calls in Zustand store
  - rapid-fire SSE events lost
  - async deduplication with eventual consistency
  - skip-and-resync pattern
  - dirty-bit for async guards
---

# Concurrent Async Guard (Skip-and-Resync)

## Overview

Skip-and-resync dirty-bit pattern for Zustand (or similar) stores with one-at-a-time async guards. Prevents rapid-fire triggers (SSE, polling, visibility) from being silently dropped. Uses atomic set() updater to close race windows. Use when syncInFlight guard causes missed events, or when concurrent async calls need eventual consistency without unbounded recursion. This skill is maintained as a `wrapper`-shaped contract: it should guide external tools, APIs, CLIs, platforms, or other side-effecting capability surfaces without stealing adjacent workflows or relying on unstated assumptions.

When a Zustand (or similar) store has a "one-at-a-time" async guard (`syncInFlight`), rapid-fire triggers (SSE events, polling, visibility changes) get silently dropped. The **skip-and-resync dirty-bit** pattern guarantees eventual consistency without unbounded recursion.

## Problem

```
SSE event A → sync starts (syncInFlight=true)
SSE event B → sync skipped (syncInFlight=true) ← LOST
SSE event C → sync skipped (syncInFlight=true) ← LOST
sync A completes → no one triggers B/C
→ 45s until next poll catches up
```

## Solution: syncPending dirty-bit + atomic capture

### State shape

```typescript
interface StoreState {
  syncInFlight: boolean;
  syncPending: boolean;   // ← NEW: dirty-bit
  // ... business fields
}
```

### Guard entry: mark dirty when skipped

```typescript
syncNotifications: async () => {
  if (get().syncInFlight) {
    set({ syncPending: true });   // mark dirty, don't execute
    return;
  }
  set({ syncInFlight: true, syncPending: false });
  // ... fetch + process
}
```

### Guard exit: atomic capture-and-clear via set() updater

**CRITICAL**: Use Zustand's `set((s) => { ... })` updater form to read `syncPending` and clear it in the same transaction. This closes the race window where a concurrent call could set `syncPending=true` between your `get()` read and your `set()` write.

```typescript
// ❌ WRONG — race window between get() and set()
const pending = get().syncPending;      // read
set({ syncInFlight: false });           // write (concurrent call can sneak in)
if (pending) void get().syncNotifications();

// ✅ CORRECT — atomic read+write inside same updater
let pending = false;
set((s) => {
  pending = s.syncPending;              // read from current state snapshot
  return {
    ...resultFields,
    syncInFlight: false,
    syncPending: false,                 // clear in same transaction
  };
});
if (pending) void get().syncNotifications();  // re-sync once
```

### Complete implementation

```typescript
syncNotifications: async () => {
  if (get().syncInFlight) {
    set({ syncPending: true });
    return;
  }
  set({ syncInFlight: true, syncPending: false });
  try {
    const res = await fetchData(get().cursor);
    if (res.success && res.data) {
      // Process data...
      let pending = false;
      set((s) => {
        pending = s.syncPending;
        return {
          ...processedData,
          syncInFlight: false,
          syncPending: false,
          error: null,
        };
      });
      void refreshImpactedStores(incoming);
      if (pending) void get().syncNotifications('sync-pending');
      return;
    }
    // Non-success: same atomic capture
    let pendingNoData = false;
    set((s) => { pendingNoData = s.syncPending; return { syncInFlight: false, syncPending: false }; });
    if (pendingNoData) void get().syncNotifications('sync-pending');
  } catch (e) {
    let pendingErr = false;
    set((s) => { pendingErr = s.syncPending; return { syncInFlight: false, syncPending: false, error: String(e) }; });
    if (pendingErr) void get().syncNotifications('sync-pending');
  }
}
```

## Why this works

| Scenario | Behavior |
|----------|----------|
| Events A, B arrive 100ms apart | A starts sync, B sets pending. A completes, captures pending, re-syncs. B's data fetched. |
| Events A, B arrive simultaneously | A enters, B sets pending. Same as above. |
| Event during re-sync | Re-sync is a normal sync call. If another event arrives during it, pending is set again, and the cycle repeats (bounded: one extra sync per missed event). |
| No concurrent events | Pending stays false, no extra sync. Zero overhead. |

## Pitfalls

1. **Never use `get().syncPending` outside a `set()` updater for the exit check.** The race window between `get()` and `set()` is real — SSE events arrive on microtask boundaries.

2. **Don't forget the error path.** If you only capture pending on success, a failed sync followed by a pending event will be stuck until the next external trigger.

3. **Don't debounce/delay the re-sync.** The whole point is minimal latency. The re-sync fires immediately after the current one completes.

4. **`syncPending` should NOT be persisted.** It's transient runtime state. Exclude it from `partialize`.

5. **Bounded recursion is safe.** Each re-sync is a fresh call that follows the same guard logic. An infinite loop requires infinite SSE events arriving during every single sync window — not possible in practice.

## When to use

- SSE/WebSocket invalidation handlers that trigger data fetches
- Visibility-change / online-event refresh handlers
- Any "trigger → fetch → update" pipeline where triggers can overlap
- Polling with concurrent manual refresh

## Related Patterns

- **Category-filtered list selection** — see `references/zustand-category-filtered-lists.md` for the pattern where a store maintains `all`, `fiat`, `crypto` (etc.) lists with different filtering semantics, and UI pickers must combine category lists rather than using `all` to preserve business rules.

## When NOT to use

- Simple one-shot fetches with no concurrent triggers
- Debounced search inputs (use debounce, not guard+dirty-bit)
- When the data source is idempotent and cheap (just re-fetch always)

## Simpler Variant: isLoading Dedup Guard

For stores that only need to prevent duplicate initial fetches (not rapid-fire SSE events), a simpler guard suffices:

```typescript
fetchAll: async () => {
  if (get().isLoading) return;  // simple dedup — no dirty-bit needed
  set({ isLoading: true, error: null });
  try {
    const data = await fetchFromAPI();
    set({ ...processData(data), isLoading: false });
  } catch (e) {
    set({ isLoading: false, error: String(e) });
  }
}
```

Use this when:
- Data is fetched once on mount, not triggered by SSE/polling/visibility
- No concurrent triggers possible (single consumer, single fetch point)
- You don't need to re-sync after a missed event

For stores with SSE, polling, or multiple trigger sources, use the full skip-and-resync pattern above.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] For mutations or external-system actions, command success was paired with target-state read-back.
