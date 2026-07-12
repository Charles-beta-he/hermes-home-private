# UVISA notification center incremental ordering

Scope: UVISA C-end notification-center tasks where newest messages appear in the middle of `/notifications`, especially after multiple in-app/SSE/push events arrive before the user opens the list.

Anti-conditions:
- Do not use for unrelated transaction/history sorting bugs.
- Do not change backend cursor semantics just to make display order convenient unless the sync contract itself is wrong.
- Do not treat right-top bell vs `我的-通知中心` as separate surfaces until routing proves they diverge; both currently route to `/notifications`.

## Symptom pattern

Lark wording like: “线上 iOS，点击右上角消息或 我的-通知中心，部分最新消息展示在列表中间，后续新推送的消息才正常显示在最上面.”

This usually means a batch of incremental notifications arrived as `event_seq ASC` and the frontend prepended the whole batch without re-sorting. Single later pushes look correct because a one-item batch placed at index 0 is trivially newest-first.

## Root-cause trace

1. Prove both user entrances share the same route:
   - `src/components/TopBar.tsx` bell link → `/notifications`
   - `src/screens/me/MeScreen.tsx` notification item → `/notifications`
   - `src/App.tsx` route → `NotificationsScreen`
2. Inspect `src/screens/home/NotificationsScreen.tsx`:
   - page calls `syncNotifications('notifications_screen_enter')`
   - list renders `notifications.filter(...)` directly; no page-level sort.
3. Inspect backend `NotificationController`:
   - full list / `afterSeq <= 0` sync sorts by `createdAt DESC, occurredAt DESC`.
   - incremental `afterSeq > 0` reads `notification_event_log ORDER BY event_seq ASC` and maps `changedIds` in that order.
4. Inspect frontend `src/stores/notification.store.ts`:
   - risky pattern is `merged = [...incoming, ...currentFiltered]` with no sort.
   - if incoming is `[new-1, new-2, new-3-latest]`, current display becomes `new-1, new-2, new-3-latest, ...`.

## Preferred fix

Keep backend event-sequence cursor semantics intact. Fix the frontend view-model boundary:

- Preserve/normalize `Notification.createdAt` from backend in `notification.service.ts` if not already present.
- In `notification.store.ts`, sort the final list after sync merge by delivery timestamp descending:
  - primary: `createdAt`
  - fallback: `occurredAt`
- Apply this to reset/full-refresh and incremental merge paths.

A minimal helper shape:

```ts
function notificationOrderTimestamp(notification: Notification): number {
  const parsed = Date.parse(notification.createdAt ?? notification.occurredAt ?? '');
  return Number.isFinite(parsed) ? parsed : 0;
}

function sortNotificationsForList(notifications: Notification[]): Notification[] {
  return [...notifications].sort((a, b) => notificationOrderTimestamp(b) - notificationOrderTimestamp(a));
}
```

## Regression test

Add a store test where:

- existing list has `old-top`, `old-mid`.
- `lastEventSeq` is non-zero.
- mocked `notificationService.sync()` returns `items` in backend event order:
  - `new-1` created at `11:35:01`
  - `new-2` created at `11:35:02`
  - `new-3-latest` created at `11:35:03`
- expected store order is:
  - `new-3-latest`, `new-2`, `new-1`, `old-top`, `old-mid`.

Run RED first and confirm it fails with received order `new-1, new-2, new-3-latest, ...`; then implement sort and run:

```bash
pnpm exec vitest run src/stores/__tests__/notification.store.test.ts --testNamePattern "keeps the newest notification first"
pnpm exec vitest run src/stores/__tests__/notification.store.test.ts src/services/__tests__/notification.service.test.ts
pnpm run build
```

## PR hygiene from the observed closeout

If the main UVISA checkout is dirty, create a clean worktree from `origin/test` (or the requested target base), apply only the scoped notification files, verify there, then open and merge a PR to the requested base. If `gh pr merge` reports local git/worktree cleanup failure, immediately read back `gh pr view <n> --json state,mergedAt,mergeCommit` and `git fetch origin <base>; git log -1 origin/<base>` before deciding whether the merge actually succeeded remotely.