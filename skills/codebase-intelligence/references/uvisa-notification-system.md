# UVISA Notification System Architecture

## Type Definition (src/types/index.ts)

```ts
export interface Notification {
  id: string;
  category: "system" | "trade" | "card" | "wealth" | "security";
  transactionType?: "deposit" | "withdrawal" | "exchange" | "card" | "wealth" | "other";
  title: string;
  body: string;        // may contain sanitized HTML
  bodyText?: string;   // plain-text preview for list rows
  time: string;
  occurredAt?: string;
  read: boolean;
  highlight?: boolean;
  target?: string;     // deep-link route
}
```

## Category Taxonomy

| category   | Tab Label (zh) | transactionType?         |
|------------|----------------|--------------------------|
| trade      | 交易           | deposit/withdrawal/exchange/card/wealth/other |
| card       | 卡片           | undefined                |
| wealth     | 理财           | undefined                |
| security   | 安全           | undefined                |
| system     | 系统           | undefined                |

Only `trade` category notifications carry a `transactionType`.

## Normalization Flow

```
Backend API → notification.service.ts:
  normalizeCategory(notification)
    → returns transactionType if present, else "other"
    → category = "trade" when transactionType exists

  normalizeNotification(raw)
    → inferTransactionType(raw) — regex on title/body keywords
    → fallback: raw.subType
```

## Inference Regexes (inferTransactionType)

```
入金/充值/到账/转入/收款    → deposit
出金/提现/转出/付款          → withdrawal
兑换/换汇/汇率              → exchange
消费/刷卡/扣费              → card
理财/收益/赎回/申购          → wealth
```

## i18n Keys (zh.json)

```
notifications.tx.deposit    → "入金"
notifications.tx.withdrawal → "出金"
notifications.tx.exchange   → "兑换"
notifications.tx.card       → "U卡"
notifications.tx.wealth     → "理财"
notifications.tx.other      → "交易"
```

## Message Center Sorting Strategy

Current user-side list rendering (`NotificationsScreen.tsx`) does not sort locally; it renders `useNotificationStore().notifications` as-is, with category tabs only filtering by `category`.

Backend intended order for `/api/notifications` and full `/api/notifications/sync?afterSeq=0` is:

1. `createdAt DESC` — primary key, interpreted as message received/inserted time; product expectation is “latest received message on top”.
2. `occurredAt DESC` — tie-breaker only, to prevent backfilled old business events from jumping ahead of newly received messages.

Key backend evidence paths:

- `api/api-public/src/main/java/com/uvisa/api/pub/NotificationController.java` — `PageRequest` uses `Sort.by(DESC, "createdAt").and(Sort.by(DESC, "occurredAt"))`.
- `domain/identity/src/main/java/com/uvisa/domain/identity/UserNotificationRepository.java` — repository methods are named `...OrderByCreatedAtDescOccurredAtDesc`.
- Historical intent commit: `d01bf0b1 fix(notif): 消息中心按 createdAt DESC 排序 — 最新收到的消息在最上方`.

Incremental `/sync` caveat: for `afterSeq > 0`, backend event query orders `notification_event_log` by `event_seq ASC`; frontend merges as `[...incoming, ...oldWithoutDuplicates]`. This means a batch of new events may not be strictly newest-first within the incoming slice, and old notifications touched by mutation events can be moved to the top. If strict ordering is required, fix either backend incremental item ordering (`createdAt DESC, occurredAt DESC`) or perform a stable store-side sort after merge using server timestamps.

### Read-status mutation reordering pitfall

Symptom: user taps an unread notification, it becomes read, then the same old row jumps to the first position in the message center.

Root cause chain:

1. `NotificationsScreen.tsx` calls `markRead(id)` before navigating to detail. Store `markRead` only performs an optimistic in-place `read: true` update; this does **not** reorder locally.
2. Backend `NotificationController.markRead()` calls `appendMutationEvent(userId, id, "notification.read", n.getType())` after saving `readAt`.
3. SSE / polling / visibility invalidation triggers `syncNotifications()`, which calls `/notifications/sync?afterSeq=lastEventSeq`.
4. Backend incremental sync treats every non-deleted event as a changed notification id; `notification.read` is included in `changedIds` and the old notification is returned in `items`.
5. Frontend merge prepends all `incoming` rows, so an existing notification touched only by read-state mutation is moved to the top.

Durable fix pattern:

- Do not prepend every incoming row blindly.
- Split incoming into `trulyNew` and `updatesForExisting` by comparing against current store ids.
- Prepend only `trulyNew`; replace existing rows in place for read/status mutations; still remove `deletedIds`.

Minimal store-side merge shape:

```ts
const current = get().notifications;
const incomingById = new Map(incoming.map((n) => [n.id, n]));
const currentIds = new Set(current.map((n) => n.id));
const updatedExisting = current
  .filter((n) => !deleted.has(n.id))
  .map((n) => incomingById.get(n.id) ?? n);
const trulyNew = incoming.filter((n) => !currentIds.has(n.id));
const merged = [...trulyNew, ...updatedExisting];
```

Backend-contract alternative: split `/sync` response into `createdItems`, `updatedItems`, and `deletedIds`; only `createdItems` should be top-inserted. Avoid using read-status changes as list-order signals.

## UI Rendering (NotificationsScreen.tsx)

- 6 horizontal scrollable tabs with unread dot indicators
- Each row: category icon (color-coded) + title + transactionType badge + body preview + time
- transactionType badge: `bg-success-soft text-success` (ALL types same green)
- highlight badge: `bg-brand-soft text-brand`
- Swipe-to-delete with confirmation bottom sheet

## Embedded Timestamp Normalization Pitfall

Scope: UVISA notification system (`uvisa-app-2.0`) only. Use this when debugging notification list/detail mismatches. Anti-condition: do not generalize this into a global rule for all app text; it applies to notification body/preview payloads that embed backend ISO instants.

Screenshot class: list row preview shows raw backend ISO/nanosecond timestamp (e.g. `2026-06-09T08:47:04.431969677Z`) while detail page shows local display time (e.g. `2026-06-09 16:47`). Root cause is usually split rendering paths:

- Detail page body uses `renderNotificationBody()` and formats embedded ISO instants before sanitizing/rendering HTML.
- List rows render `n.bodyText ?? n.body` directly from store, so any backend preview/body string must be normalized before it enters the notification store.

Durable fix pattern:

- Keep one shared helper for embedded notification-body times, e.g. `src/lib/notificationTime.ts::formatNotificationEmbeddedTimes()`.
- Reuse it in both `src/lib/notificationBody.ts` and `src/services/notification.service.ts::normalizeNotification()`.
- Normalize both `body` and `bodyText`/`preview`; do not only normalize `notification.time` or detail rendering.
- Tests should include Java/Instant nanoseconds (`.431969677Z`) and assert raw ISO is absent from both `body` and `bodyText` after `normalizeNotification()`.

## Impact Router (notificationImpactRouter.ts)

Maps notification category/sub-type to store refreshes:
```
trade category  → refresh: wallet, transactions
  + transactionType=card   → also refresh: card
  + transactionType=wealth → also refresh: wealth
card category   → refresh: card
wealth category → refresh: wealth
```

## Toast Component — Timestamp Extension

The `Toast` component (`src/components/ui/Toast.tsx`) was extended to support a `timestamp` prop for displaying relative time (e.g., "Now", "刚刚") on the right side of the banner.

```tsx
// Interface extension
interface ToastItem {
  // ... existing fields
  timestamp?: string; // optional, rendered right-aligned
}

// Usage pattern — options object form
toast(t("notifications.markAllReadDone"), {
  tone: "success",
  timestamp: t("time.justNow"), // "刚刚" / "Now"
});
```

Rendering: timestamp appears right-aligned before the dismiss button when present.

## Mark-All-Read Pattern

```ts
// Store action (useNotificationStore)
markAllRead: async () => {
  const prev = get().notifications;
  const unread = prev.filter(n => !n.read);
  set({
    notifications: prev.map(n => ({ ...n, read: true })),
    unreadCount: { total: 0, byCategory: {} },
  });
  try {
    await notificationService.markAllAsRead();
  } catch {
    // Revert on failure
    set({
      notifications: prev,
      unreadCount: countUnread(prev),
    });
    toast(t("notifications.markReadFailed"), "error");
  }
},
```

UI feedback: Toast with `tone="success"` and `timestamp` showing current time.

## i18n Keys

```
notifications.markAllReadDone → "已全部标记为已读" / "All marked as read"
notifications.markReadFailed  → "标记已读失败，请重试" / "Failed to mark as read"
time.justNow                  → "刚刚" / "Just now"
```

## UX Gap (observed)

All transactionType badges share the same green color (`bg-success-soft text-success`). Deposit vs withdrawal are distinguishable only by text content, not by visual color. Consider:
- deposit → green (positive/money-in)
- withdrawal → red/orange (negative/money-out)
- exchange → blue (neutral)
