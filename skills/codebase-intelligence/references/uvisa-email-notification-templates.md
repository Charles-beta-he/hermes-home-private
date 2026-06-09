# UVISA Email Notification Template Architecture

## Two-Layer System

Email notifications in UVISA have a **non-obvious two-layer architecture**:

1. **Java code** — hardcoded title/body string literals passed as variables
2. **DB templates** — HTML email shell seeded via Flyway, wraps the title/body

The template does NOT contain the message content. It only provides the visual shell.

## Layer 1: Hardcoded Messages (Java)

Messages are hardcoded as string literals at the call site, NOT in templates.

### GsalaryWebhookController.java (webhook callback path)

| Trigger | Title | Body pattern |
|---------|-------|-------------|
| REMITTANCE_COMPLETE | "汇款已到账" | "您的汇款({amount})已成功到账。" |
| Settlement failed | "出金失败，资金已退回" | "您的汇款({amount})处理失败..." |
| Returned/退回 | "汇款被退回,资金已退回" | "您的汇款({amount})被退回..." |
| Transfer failed | "汇款失败,资金已退回" | "您的汇款({amount})处理失败..." |

### PayoutAdminFacade.java (admin manual operations)

| Trigger | Title | Body pattern |
|---------|-------|-------------|
| markSettled() | "出金已到账" | "您的出金申请({amount} {currency})已成功到账。" |
| markFailed() | "出金失败" | "您的出金申请({amount} {currency})处理失败,冻结资金将通过退款流程退回,如有疑问请联系客服。" |

### Sending mechanism

Both paths call `notifyPayoutTerminal()` / `notifyTerminal()` which invoke:
```java
notify.notifyUserWithTemplate(userId, "PAYOUT", title, body,
    Instant.now(), relatedJournalId, referenceId,
    NotificationTemplateCode.PAYOUT_TERMINAL,
    Map.of("title", title, "body", body),
    NotificationChannel.Type.EMAIL);
```

The title/body are passed TWICE: once for station notification (plain text), once as template variables for email HTML rendering.

## Layer 2: DB Templates (Flyway)

Seeded in `V10120__notification_template_5locales.sql`.

| Template Code | Purpose |
|--------------|---------|
| `payout.terminal` | HTML shell for terminal-state payout emails. Variables: `{{title}}`, `{{body}}` |
| `payout.usdt_submitted` | USDT payout submitted confirmation |
| `payout.cny_submitted` | CNY payout submitted confirmation |
| `payout.refunded` | Payout refund notification |

## Template Code Enum

`NotificationTemplateCode.java` defines the enum mapping:
- `PAYOUT_TERMINAL("payout.terminal")`
- `PAYOUT_USDT_SUBMITTED("payout.usdt_submitted")`
- `PAYOUT_CNY_SUBMITTED("payout.cny_submitted")`
- `PAYOUT_REFUNDED("payout.refunded")`

Admin UI can also send templates via `POST /api/admin/notification-templates/send` using raw String codes (not limited to enum values).

## Key Files

- `domain/notification/.../NotificationTemplateCode.java` — enum
- `domain/notification/.../NotificationDispatcher.java` — dispatch logic, dedup by referenceId
- `domain/notification/.../TemplatedEmailSender.java` — HTML rendering
- `app/uvisa-app/.../webhooks/GsalaryWebhookController.java` — webhook-triggered notifications
- `api/api-admin/.../outflow/PayoutAdminFacade.java` — admin-triggered notifications
- `db/migration-mysql/V10120__notification_template_5locales.sql` — template seed data

## Debugging Checklist

1. **Message content wrong?** → Search Java call sites for hardcoded strings, NOT the DB template
2. **Email visual/layout wrong?** → Check `notification_template` table (Flyway seed or admin UI edits)
3. **Email not sent at all?** → Check `NotificationDispatcher` logs, dedup by referenceId, user email lookup
4. **i18n missing?** → Template has 5 locale variants (V10120), but Java hardcoded strings are Chinese-only
5. **Want to change message without code deploy?** → Not possible with current architecture; title/body are in Java

## Anti-patterns

- Searching admin UI config for message content (it's not there)
- Assuming templates contain the actual message text (they only wrap it)
- Modifying Flyway seed SQL to change messages (only changes the HTML shell, not content)
