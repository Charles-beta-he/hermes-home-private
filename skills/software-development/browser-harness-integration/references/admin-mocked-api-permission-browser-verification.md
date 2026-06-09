# Admin mocked-API browser verification pattern

Use this when a protected admin page needs browser-level closure but real credentials or mutable production data are unavailable. It verifies the UI contract without leaking or depending on secrets.

## When to use

- Admin routes guarded by session/local storage auth and permission APIs.
- Product/prototype closure requires visual and interaction evidence.
- The page depends on backend data, but the specific UI behavior can be verified with deterministic fixtures.
- Sensitive operations require GA/OTP confirmation, and the test should verify that the UI sends `gaCode` without performing a real production action.

## Pattern

1. Start the local Vite/admin server normally.
2. Use Playwright with an installed local browser if Playwright-managed browser download is unavailable:
   - Prefer `chromium.launch({ headless: true })` when the bundled browser exists.
   - Fallback: `chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' })` on macOS.
3. Inject admin auth state before navigation:
   - `sessionStorage.setItem('uv:admin:at', '<test-token>')`
   - `localStorage.setItem('uv:admin:rt', '<test-refresh>')`
   - `sessionStorage.setItem('uv:admin:profile', JSON.stringify({ passwordMustChange: false, totpEnabled: true, ... }))`
4. Route/intercept `/api/admin/**` requests and return deterministic envelopes matching the app's API shape.
5. Test at least two permission profiles:
   - Full permission profile: assert raw fields and privileged buttons are visible.
   - Restricted profile: assert raw PII is absent, masked/hidden values appear, and privileged buttons are absent.
6. Capture request evidence for behavior that is not purely visual:
   - Pagination should show `/api/admin/users?page=2&size=50` after clicking next page.
   - GA-gated operations should POST the entered code, e.g. `{ "gaCode": "123456" }`.
7. Save screenshots and a machine-readable `summary.json` containing verdict, checks, API calls, console errors, page errors, and request failures.
8. Treat the browser run as UI/interaction proof, not as real business-data integration, unless it used a real test environment and real login.

## Pitfalls

- Do not hard-code or persist real access tokens, refresh tokens, passwords, OTP secrets, or credentials. Use test placeholders only.
- Do not claim real write-path integration if the backend was mocked. Phrase the result as `mocked-auth/mocked-api browser verification`.
- Layout/menu components may fire unrelated dashboard badge APIs; route them too so they do not produce noise.
- Assert both presence and absence: privileged UI visible with permissions, hidden without permissions; raw PII visible only with field permissions, absent without them.
