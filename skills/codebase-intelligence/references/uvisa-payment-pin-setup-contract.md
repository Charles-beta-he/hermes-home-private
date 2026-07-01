# UVISA payment PIN setup contract

Applicability: Use for UVISA 2.0 questions or debugging around first-time "设置支付密码 / 设置交易 PIN / payment PIN setup" in the C-side app. Re-verify current code before making implementation or production claims.

Anti-conditions: Do not use this as a general password-change map. Verification and change flows have separate endpoints. Do not assume the frontend already uses the ME-domain endpoint just because the backend exposes it.

## Current contract map

Frontend current-state evidence path:
- `uvisa-app-2.0/src/services/auth.service.ts`
- `authService.setupPin(payload)` posts to `'/auth/pin/setup'`.
- Axios `baseURL` is `/api` from `src/lib/api.ts`, so the actual browser request is:
  - `POST /api/auth/pin/setup`

Frontend payload shape:

```json
{
  "encPin": "...",
  "encConfirmPin": "..."
}
```

Backend legacy/current frontend-compatible endpoint:
- `uvisa-backend/api/api-public/src/main/java/com/uvisa/api/pub/LegacyApiController.java`
- `@PostMapping("/api/auth/pin/setup")`
- Resolves `pin/encPin` and `confirmPin/encConfirmPin`; rejects mismatched values; calls `paymentPinService.setPin(userId, pin)`; returns `success: true`.

Backend ME-domain setup endpoint:
- `uvisa-backend/api/api-public/src/main/java/com/uvisa/api/pub/MeController.java`
- class mapping `@RequestMapping("/api/me")`; method `@PostMapping("/payment-pin")`.
- Actual endpoint:
  - `POST /api/me/payment-pin`
- Payload shape:

```json
{
  "encPin": "..."
}
```

## Answering rule

When the user asks "设置支付密码的接口是什么":

1. If they mean the current app screen / frontend call, answer `POST /api/auth/pin/setup`.
2. Mention that the backend also exposes the ME-domain endpoint `POST /api/me/payment-pin`.
3. Distinguish setup from verify/change:
   - setup current frontend: `POST /api/auth/pin/setup`
   - setup ME-domain backend: `POST /api/me/payment-pin`
   - verify auth-domain: `POST /api/auth/pin/verify`
   - verify ME-domain: `POST /api/me/payment-pin/verify`
   - change auth-domain: `POST /api/auth/pin/change`
   - change ME-domain: `POST /api/me/payment-pin/change`
4. State code evidence paths and line ranges from a fresh read/search whenever possible.

## Token replacement after first-login PIN setup

When the requirement is "新用户支付密码设置成功后替换正式 token" and the boundary is **frontend-only / do not change backend**:

1. Keep the current setup call as `authService.setupPin()` → `POST /api/auth/pin/setup`.
2. Preserve login-token field compatibility with other auth flows:
   - login/verify token body uses `token` alias plus `accessToken`, `refreshToken`, `user`;
   - frontend consumers should read access token as `data.token ?? data.accessToken`;
   - refresh responses may only include `accessToken`/`refreshToken` and no `user`.
3. On setup success:
   - if the setup response already contains `token/accessToken + user`, pass it through the same auth-token consumer used by OTP/password login;
   - otherwise call existing `authService.refreshToken()` and replace `localStorage.auth_token`, `localStorage.refresh_token`, Zustand `token`, and Zustand `refreshToken` from `refresh.data.token ?? refresh.data.accessToken` / `refresh.data.refreshToken`;
   - keep the current user object and set `user.hasPaymentPin=true` after successful setup.
4. Add frontend tests for both compatibility paths:
   - setup endpoint directly returns a post-setup token pair;
   - current backend returns no token pair, so frontend refreshes and replaces the local token pair.
5. If backend changes are allowed in a future task, the canonical backend-compatible shape should match login `tokenBody`: `accessToken`, `refreshToken`, `expiresInSec`, `token`, `currentDeviceTrusted`, `user`.

## Frontend-only token replacement boundary

When the user asks to replace the token after first-time Payment PIN setup, first clarify whether backend changes are allowed. If the user says not to modify backend code, do **not** add backend tests or change `LegacyApiController`/token issuance. Implement the C-side compatibility path only:

1. Keep current `POST /api/auth/pin/setup` as the setup endpoint.
2. If the setup response already contains the login-compatible token contract (`token` or `accessToken`, plus `refreshToken`, and `user` when consuming full auth state), consume it with the same logic as OTP/password login (`token ?? accessToken`).
3. For the current backend shape where setup returns only `{ success: true }`, call existing `POST /api/auth/refresh` immediately after setup success and replace local `auth_token` / `refresh_token` plus Zustand auth token state.
4. Preserve existing user state and set `hasPaymentPin: true`; refresh does not return `user`.
5. Add front-end store tests for both response shapes: setup returns token pair, and setup returns no token so refresh replaces tokens.
6. Verify with focused auth-store tests and `pnpm build`. Use a clean temporary worktree for PRs if the main checkout has unrelated WIP.

Applicability: UVISA C-side first-login Payment PIN setup and token lifecycle only. Anti-condition: if the product explicitly requires temporary-token-to-formal-token semantics enforced by backend authority, frontend refresh is only a compatibility layer; backend token issuance requires separate explicit permission.

## Pitfalls

- The UI may say "支付密码", but much of the C-side flow is a 6-digit payment PIN, not an alphanumeric payment password.
- `api.post('/auth/pin/setup')` becomes `/api/auth/pin/setup` because axios `baseURL` is `/api`.
- Do not collapse `/auth/pin/setup` and `/me/payment-pin` into one answer without saying which caller/domain uses which endpoint.
- For first-login routing, cross-check `hasPaymentPin/paymentPinSet` gates before blaming the endpoint.
- Do not start backend RED tests or controller edits when the user has constrained the task to frontend-only token replacement.
- Do not assume payment PIN setup response fields without comparing them to OTP/password login and refresh contracts; login consumes `token ?? accessToken` with `refreshToken` and `user`, while refresh may not include `user`.
