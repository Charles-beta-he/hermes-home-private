# Root-Cause Ownership Council Calibration Domains

Version: 1.0.0
Purpose: domain classes where the council role is already calibrated enough to be useful. These are not project-specific facts and must be re-grounded in the target repo before implementation.

## Calibrated domains

### Mobile keyboard / viewport / layout

Common failure mechanism:
- Visible symptom appears in header, CTA, or input.
- Real problem is ownership conflict across visual viewport, document/body scroll, route scroller, component shell, and global focus handlers.

Key variables:
- viewport height
- document/body scroll
- route scroll
- focused input visibility
- CTA placement
- safe-area and tabbar reserve
- overlay/panel scroll

Typical contrast paths:
- ordinary form input
- chat composer
- short login/auth
- sheet/modal
- preview/confirm/detail

### Error surface / auth / API interceptor

Common failure mechanism:
- API interceptor, auth store, page toast, and global network toast all decide user-visible errors.

Key variables:
- 401 refresh/session expiration
- SSO kick vs normal expiry
- 4xx business error owner
- 5xx server error message owner
- no-response network failure
- cancellation/navigation abort

Typical contrast paths:
- 4xx backend message handled by page
- 5xx backend message handled by global surface
- pure network error generic
- cancellation silent
- auth-expired event distinct from business failure

### Notification / SSE / WebPush

Common failure mechanism:
- In-app truth, realtime invalidation, account preference, and device subscription are collapsed into one UI switch or store update.

Key variables:
- notification sync cursor / event sequence
- unread count
- category counts
- account-level notification preference
- current-device push subscription
- browser permission / capability
- SSE/SW/focus/bootstrap invalidation triggers

Typical contrast paths:
- server sync after event invalidation
- stale cursor recovery
- unsupported browser/device
- permission denied
- account preference true but this device unavailable

### Client release / service worker / PWA update

Common failure mechanism:
- Service worker asset freshness, backend release policy, update UI, and bad-release rollback each try to decide reload/update timing.

Key variables:
- backend release manifest
- current release id
- pending release id
- service worker waiting/controllerchange
- safe boundary
- force reload
- bad release mark / rollback target
- update banner visibility

Typical contrast paths:
- stale asset but unsafe route
- backend pending release but SW not ready
- SW update but backend policy not aligned
- chunk load failure
- boot success vs watchdog timeout

### Payment / remit / card business flow

Common failure mechanism:
- UI, service, backend response, and copy each imply business state; amount precision and CTA enablement drift from backend contract.

Key variables:
- amount decimal string
- fee quote
- available balance
- limit warning
- recipient/counterparty label
- order/transaction status
- CTA enabled/disabled
- preview/confirm/detail split

Typical contrast paths:
- tiny decimal amounts
- fee quote changes
- limit warning without invented frontend risk decision
- backend status display
- detail page vs input page

### Customer service / chat / composer

Common failure mechanism:
- public customer-service entry, authenticated session, chat composer, upload rules, and keyboard behavior are mixed.

Key variables:
- public entry availability
- authenticated session fetch
- active chat session state
- composer keyboard mode
- upload MIME/size/sanitization
- FAQ/AI routes

Typical contrast paths:
- unauthenticated support entry
- authenticated chat session
- image upload including HEIC/HEIF
- composer keyboard behavior
- update/banner/header overlays

## Migration rule

When using this calibration in a new task:

1. Re-read target source/tests/history.
2. Confirm the same failure mechanism exists.
3. Strip local project names and paths from any durable lesson.
4. Build a fresh owner table and evidence ledger.
5. Only transfer method and scenario taxonomy, not concrete code conclusions.
