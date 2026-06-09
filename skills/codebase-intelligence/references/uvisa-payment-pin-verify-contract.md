# Scoped reference: UVISA payment PIN verify contract mapping

SCOPE / APPLICABILITY:
- Applies only to the UVISA 2.0 C-side frontend/backend codebases when analyzing or changing payment PIN verification flows.
- Frontend repo scope: `/Users/charles/Desktop/folder/work/uvisa-app-2.0`.
- Backend repo scope: `/Users/charles/Desktop/folder/work/uvisa-backend`.
- Use this as a project-scoped reference under the class-level codebase-intelligence skill; do not generalize these endpoint names, route names, or scene labels to other projects.

ANTI-CONDITIONS:
- Do not apply this to non-UVISA projects.
- Do not treat this as a universal authentication/PIN design rule.
- Do not infer current production deployment state from this reference; always inspect live code before making claims.
- Do not preserve stale task/commit status from this reference; it is only a reusable mapping/checklist.

## Frontend surfaces

Main service wrapper:
- `src/services/auth.service.ts`
  - `verifyPaymentPassword(pin, options?)` → `/auth/pin/verify`
  - `verifyMyPaymentPin(pin, options?)` → `/me/payment-pin/verify`
  - request body is built from `encField(...)` plus optional `{ type, purpose }`
  - encryption path returns only `encPin`; fallback returns only `pin`; metadata must be merged after encryption fallback.

Unified flow:
- `src/screens/payment/PaymentVerifyScreens.tsx`
  - route `/pay/verify/pin`
  - infers `type` from `next` URL before calling `verifyPaymentPassword`
  - typical mapping: `/exchange/*`→`exchange`, `/payout/*`→`payout`, `/remit/*`→`remit`, `/card/*`→`card`, `/wealth/*`→`wealth`, fallback sensitive settings→`settings`.

Direct verify surfaces that should carry explicit scene metadata:
- `src/screens/auth/VerifyPinOnLoginScreen.tsx` → `type: 'login'`
- `src/screens/card/CardCvvScreen.tsx` → `type: 'card'`
- `src/screens/remit/RemitPasswordScreen.tsx` → `type: 'remit'`
- `src/screens/me/ChangePaymentPwdScreen.tsx` → `type: 'settings'`
- `src/screens/me/security/ChangeEmailScreen.tsx` → `type: 'settings'`
- `src/screens/me/security/ChangePhoneScreen.tsx` → `type: 'settings', purpose: 'phone-rebind'`

## Backend contract facts

Legacy endpoint:
- `api/api-public/src/main/java/com/uvisa/api/pub/LegacyApiController.java`
- `POST /api/auth/pin/verify`
- accepts `pin`, `encPin`, `purpose`; frontend may also send `type` only when current backend contract supports or safely ignores it. Verify Jackson/DTO behavior in live code before relying on extra fields.
- `purpose === 'phone-rebind'` writes phone-rebind step-up Redis flag.

ME endpoint:
- `api/api-public/src/main/java/com/uvisa/api/pub/MeController.java`
- `POST /api/me/payment-pin/verify`
- accepts `pin`, `encPin`, `purpose`
- `purpose === 'phone-rebind'` writes the same phone-rebind step-up flag.

Important: phone rebind is the high-risk special case. Backend docs require payment PIN verification with `purpose: 'phone-rebind'` before later new-phone verification/request-new-code gates. If ChangePhoneScreen only sends the PIN without purpose, later backend step-up gates may fail despite correct PIN.

## UI error-message pass-through audit (UVISA-scoped)

SCOPE / APPLICABILITY: this subsection applies only to the UVISA 2.0 C-side frontend payment PIN/payment-password verification surfaces listed in this reference. ANTI-CONDITIONS: do not generalize these route/file names or exact Chinese copies to other projects; always inspect current UVISA source before making a claim.

When the task asks whether payment PIN/payment-password screens match backend-returned status/message, audit both layers:

1. Service wrapper must expose backend `message` as `res.error`:
   - `verifyPaymentPassword(...)` maps adapted envelope `data.message` to `error`.
   - `verifyMyPaymentPin(...)` and legacy `verifyMyPaymentPassword(...)` must preserve `data.message` on non-success and caught 4xx responses.
2. UI callsites must pass that `res.error` into the visible error surface. For top-banner PIN failures, post-response branches should call:
   - `showPinErrorBanner(toast, t, lockedOrPostBlocked, res.error)`
   not just `showPinErrorBanner(toast, t, post.blocked)`.
3. Do not confuse local pre-block guards with backend responses:
   - `getGuardState("payment-pin").blocked` happens before a request and has no backend message to pass; fallback i18n is acceptable there.
   - Any branch after `verifyPaymentPassword` / `verifyMyPaymentPin` returns should prefer the backend message so copy like `支付密码错误，还可尝试3次` is not replaced by static fallback copy like `请重新输入，连续错误 5 次将锁定账户`.
4. Include all direct UVISA surfaces in the scan: login PIN, card CVV reveal, change payment password, change email, change phone, unified payment verify, remittance password.

Regression pattern that worked: add a small source-scan Vitest under `src/lib/__tests__/...` that lists the UVISA payment PIN screen files and fails if any post-response `showPinErrorBanner(...)` call omits `res.error`, while allowing pre-request `pre.blocked` local-guard calls.

## Testing pattern

Use TDD when changing this UVISA-scoped contract:
1. Service-level RED tests in `src/services/__tests__/auth.service.test.ts` asserting metadata survives encryption fallback, e.g. body `{ pin: '888888', type: 'exchange' }` or `{ pin: '888888', purpose: 'phone-rebind' }`.
2. Route inference tests in `src/screens/payment/__tests__/paymentVerifyType.test.ts` for the `next` URL mapping.
3. Flow tests for special-purpose callers, especially phone rebind asserting `verifyMyPaymentPin('888888', { type: 'settings', purpose: 'phone-rebind' })`.
4. Message-pass-through tests for UI callsites: backend `message` → service `res.error` → banner/toast body, including both locked and pre-lockout remaining-attempt messages.
5. Run targeted vitest first, then `pnpm test -- --reporter=dot`, then `pnpm run build`.

Known existing noise: some React Testing Library tests emit `act(...)` warnings while still passing. Do not treat those warnings alone as a regression unless the touched test starts failing or warning volume clearly changes around touched code.
