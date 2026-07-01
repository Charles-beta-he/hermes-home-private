# UVISA notification template CTA contract

Scope: UVISA C-end Lark tasks about Notification Center / message detail bottom CTA buttons, especially wording like “根据后台配置项是否配置来判断是否显示”, “改模板”, “查看持仓”, “通知中心”, “理财已到期”.

Anti-conditions: Do not apply to unrelated static page buttons, tab-bar navigation, or Lark closeout/writeback. This reference is intake/implementation guidance only; final Lark completion still needs the normal online UI evidence and native screenshot gates.

## Key lesson

Do not assume changing an in-app template `cta_text` is sufficient. In the current UVISA architecture, a template may store `in_app_template_locale.cta_text`, but the C-end notification detail screen may still render a bottom button from frontend category fallback logic.

Observed pattern:

- Backend seed/template tables have per-locale `cta_text` in `in_app_template_locale`.
- `InAppMessageSender` can render title/body into `identity_user_notification`, but may not snapshot `cta_text` into the user notification row.
- `NotificationController.toItem()` may return only `id/type/category/title/body/bodyText/read/time/...`, with no `ctaText` / `ctaTarget` contract.
- Frontend `NotificationDetailScreen` may compute `ctaTarget = notification.target ?? fallbackTarget(notification.category)` and map `category=wealth` to a default button label such as `notifications.viewWealth` / “查看持仓”.

Therefore, a task saying “product confirmed: remove the bottom ‘查看持仓’ button; just change the template” should be treated as a CTA contract task, not as a seed-file-only edit.

## Intake checklist

1. Read the Lark task comments, not just the title. If comments say “去掉按钮 / 改模板”, preserve both as acceptance atoms.
2. Inspect backend template seeds/migrations for the exact template key and locale rows:
   - `in_app_template`
   - `in_app_template_locale.cta_text`
   - email `notification_template*` if the task also touches email/push, but do not conflate email templates with C-end in-app UI.
3. Inspect sender and API projection:
   - Does `InAppMessageSender` snapshot CTA text/target into `identity_user_notification` or a linked record?
   - Does `NotificationController.toItem()` expose a CTA field to `/api/notifications`, `/sync`, and `/{id}`?
4. Inspect frontend display logic:
   - Is a bottom CTA rendered from backend fields only?
   - Or is there a category fallback such as `wealth -> /wealth` with fixed label “查看持仓”?
5. Atomize entry paths separately when named by the task:
   - top-right message entry -> detail
   - My -> Notification Center -> detail
   - detail bottom CTA visibility

## Implementation guidance

Preferred contract-shaped fix:

1. Backend template change:
   - Set the target template’s `cta_text` to `NULL` or empty per product decision.
   - For already-deployed DBs, add a new Flyway `UPDATE`; do not only edit old seed files.
   - Keep template scope narrow. Example: `WEALTH_MATURED` may need no CTA, while `WEALTH_MATURITY_REMINDER` may still need “查看持仓”. Do not delete every wealth CTA unless product explicitly says so.
2. Backend API projection:
   - Expose optional CTA fields (`ctaText`, `ctaTarget`/`target`, or equivalent) from the in-app notification contract.
   - If `cta_text` is `NULL`, return no CTA / null so the frontend can hide the action.
   - Keep `/api/notifications`, `/api/notifications/sync`, and `/api/notifications/{id}` consistent.
3. Frontend display:
   - Remove or gate category-only fallback CTAs for notification detail when the task says visibility depends on backend configuration.
   - Render the bottom primary CTA only when the backend explicitly provides CTA config.
   - If no CTA exists, show the product-approved fallback (often “返回消息中心”) or no fixed bottom CTA; do not silently substitute “查看持仓”.
4. Tests:
   - Backend: template with `cta_text=NULL` projects no CTA; template with CTA still projects it.
   - Frontend: wealth matured notification with no backend CTA does not show “查看持仓”; notification with explicit CTA does show and navigate.
   - Regression: existing trade/security/card notifications keep their intended CTA only when backed by config.

## Pitfalls

- “改模板就可以了” can be true product intent but false technically if the frontend has hardcoded category fallback.
- Removing all wealth-category fallback blindly can break reminders or interest-paid messages that still need an action.
- Editing old Flyway seed files does not change already-applied environments; add a new migration/update for live DB behavior.
- Lark Task comment images may appear only as `[Image]` placeholders through the Task API. Treat that as API-limited evidence, not absence of screenshots.
