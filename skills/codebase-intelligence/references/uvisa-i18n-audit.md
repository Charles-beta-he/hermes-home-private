# UVISA i18n Audit Patterns

## Architecture Overview

| Layer | File/Location | Format |
|-------|--------------|--------|
| Frontend zh | `src/i18n/zh.json` | Flat key-value, dot-separated namespace |
| Frontend en | `src/i18n/en.json` | Same structure, parallel keys |
| Frontend component | `useTranslation()` + `t("key")` | React-i18next hook |
| Backend error codes | `api/api-common/.../ErrorCode.java` | `@I18nEn`/`@I18nZh` annotations |
| Backend resolution | `MessageSourceAutoConfiguration` | `error.{snake_case}` message keys |
| Backend exceptions | `BizException(ErrorCode)` → `GlobalExceptionHandler` | Locale-aware message resolution |

## Frontend i18n Key Namespaces (Order Detail)

| Namespace | Purpose | Example Keys |
|-----------|---------|-------------|
| `order.*` | Order detail page | `order.title`, `order.orderId`, `order.status` |
| `order.title.*` | Status-specific titles | `order.title.payoutCnyFailed` = "提现失败" |
| `order.sub.*` | Status-specific subtitles with interpolation | `order.sub.payoutCnyFailed` = "{{amount}} 提现失败" |
| `order.timeline.*` | Timeline node labels | `order.timeline.cny.submitted`, `order.timeline.payout.onchain` |
| `order.channel.*` | Channel display names | `order.channel.realtimeOnshore` = "境内实时到账" |
| `order.arriveCard` | Arriving card label | "到账卡" / "Arriving Card" |
| `order.failReason` | Failure reason heading | "失败原因" / "Failure reason" |
| `order.failedNotice` | Failure notice body | Full sentence about cancellation |
| `common.*` | Shared buttons | `common.contactSupport`, `common.goHome` |

## Audit Checklist: Frontend Component

For any screen with i18n:

1. **Extract all user-visible strings** from the component JSX
2. **Grep `src/i18n/zh.json`** for matching keys — verify zh translation exists
3. **Grep `src/i18n/en.json`** for matching keys — verify en translation exists
4. **Check interpolation**: `{{var}}` syntax in both zh and en must match
5. **Check dynamic values**: channel names, status labels that come from backend — are they translated via key lookup or raw-displayed?
6. **Check hardcoded strings**: any Chinese/English literals in JSX that bypass `t()`

## Backend Error Message Flow

```
BizException(ErrorCode.XXX)
  → GlobalExceptionHandler.resolveMessage(effectiveLocale)
    → messageSource.getMessage("error.xxx", args, locale)
      → @I18nEn / @I18nZh annotations on ErrorCode enum
```

**Key pitfall**: `BizException(ErrorCode, detailMessage)` — if `detailMessage` is provided, it OVERRIDES the i18n resolution. The `GlobalExceptionHandler` checks `e.getMessage()` first; if non-blank, it uses that instead of resolving from `ErrorCode`.

## Backend Hardcoded Chinese — Known Locations

### TransactionAggregationService (domain/identity/)

Timeline node descriptions are hardcoded Chinese strings, NOT i18n-resolved:

| Node | Hardcoded String | When |
|------|-----------------|------|
| OPS review | `"自动放行（命中阈值），跳过 OPS 初审"` | Auto-released |
| OPS review | `opAdminName + " 初审通过"` | Manual pass |
| OPS review | `"OPS 已驳回：" + rejectReason` | Rejected |
| Treasury review | `"自动放行（命中阈值），跳过技术终审"` | Auto-released |
| Treasury review | `treasuryAdminName + " 标准额度，单审复核"` | Manual pass |
| Channel send | `"通道发送失败：" + failedReason` | Channel failed |
| Channel send | `"等待通道推送"` | Pending |
| Settlement | `"已退款：" + failedReason` | Refunded |
| Settlement | `"通道返回失败：" + failedReason` | Channel returned failed |

**Impact**: When frontend reads timeline nodes from `TransactionController.details`, these descriptions are in Chinese regardless of user locale. The frontend `PaymentDetailScreen` uses its own `TIMELINE_I18N` mapping for step titles (which ARE i18n'd), but the backend `description` field is displayed as-is.

### failReason Field — Untranslated Upstream Errors

The `failedReason` field in `payout_intent` table stores raw error messages from upstream services (Gsalary, Cobo, SWIFT gateway). These are:
- English technical messages ("Resource not found", "Insufficient balance")
- Sometimes Chinese from domestic channels
- Never passed through i18n resolution

**Data flow**: Upstream API → `GsalaryPayoutOrder.failedReason` / `PayoutOrderAdmin.failedReason` → DB column `failed_reason` → `TransactionAggregationService` timeline description → frontend `details.failedReason`

**Frontend display**: `PaymentDetailScreen` shows `tx.failReason` directly under `t("order.failReason")` heading. The heading is i18n'd but the value is raw.

## Channel Translation Issues

`order.channel.realtimeOnshore` = "Rights card real-time" — semantically incorrect. Should be "Domestic real-time" or "CNY real-time" (境内实时到账 means domestic/CNY real-time arrival).

## How to Audit a New Screen

```bash
# 1. Find all t() calls in the component
grep -oP 't\(["'"'"']([^"'"'"']+)["'"'"']' src/screens/TargetScreen.tsx | sort -u

# 2. Check zh coverage
for key in $(grep -oP 't\(["'"'"']\K[^"'"'"']+'); do
  grep -q "\"$key\"" src/i18n/zh.json || echo "MISSING zh: $key"
done

# 3. Check en coverage
for key in $(grep -oP 't\(["'"'"']\K[^"'"'"']+'); do
  grep -q "\"$key\"" src/i18n/en.json || echo "MISSING en: $key"
done

# 4. Find hardcoded Chinese in JSX
grep -P '[\x{4e00}-\x{9fff}]' src/screens/TargetScreen.tsx

# 5. Check backend description fields for hardcoded strings
grep -rn "put(\"description\"" domain/ --include="*.java" | grep -P '[\x{4e00}-\x{9fff}]'
```

## Backend i18n Resolution Fix Pattern

For `BizException` with detail messages that should be i18n'd:

```java
// WRONG — detail message bypasses i18n
throw new BizException(ErrorCode.NOT_FOUND, "Resource not found");

// RIGHT — let ErrorCode annotations drive resolution
throw new BizException(ErrorCode.NOT_FOUND);

// RIGHT — if args needed for interpolation
throw new BizException(ErrorCode.NOT_FOUND, resourceType);
// with @I18nZh("未找到{0}资源") on ErrorCode.NOT_FOUND
```

For `TransactionAggregationService` timeline descriptions, the fix requires either:
1. Moving descriptions to i18n keys and returning key+args instead of final text
2. Or accepting Chinese-only backend descriptions and letting frontend override with its own TIMELINE_I18N mapping (current partial approach)
