# Mocked auth + mocked API browser verification for auth-gated local admin pages

Use this pattern when all of the following are true:
- the task is frontend/UI validation rather than real auth/business-write acceptance;
- build/unit checks already cover logic correctness;
- direct browser storage injection is unstable because app bootstrap/profile fetching clears or overwrites the fake session;
- you still need real rendered-page evidence across desktop/mobile viewports.

Recommended sequence
1. Build first (`npm run build`) so type and bundling regressions fail before browser work.
2. Start the local dev server and verify health with curl.
3. Prefer browser-harness/real browser first. Try the minimal mocked auth state only once you have inspected the real auth store shape.
4. If the app immediately redirects back to login because startup code revalidates profile/permissions, switch to a deterministic Playwright script instead of fighting storage hydration.
5. In the Playwright script:
   - launch a local browser (system Chrome is acceptable if bundled Playwright Chromium is unavailable);
   - seed the exact auth storage keys the app expects;
   - intercept profile/permission/bootstrap endpoints and return a stable authenticated envelope;
   - intercept page-level APIs with compact fixtures that exercise the changed UI states;
   - run both desktop (1280) and mobile (375) viewports;
   - record screenshots, console errors, page errors, and a JSON summary into a stable temp directory (for example `/tmp/<project>-<scope>-<date>`).
6. Keep the scope label precise: this is `mocked-auth + mocked-API browser UI verification`, not backend acceptance, not permission acceptance, and not proof of business-write semantics.
7. After the script passes, visually inspect at least one desktop and one mobile screenshot for obvious layout issues that automation may miss.

High-value fixture coverage for admin pages
- Dashboard: include the newly added metric/tile so the page proves the feature actually renders.
- Records/list pages: include one realistic row that surfaces the fields added in the patch.
- Detail drawers/modals: include one clickable entity so mobile overlay width/overflow problems become visible.
- Secondary bootstrap APIs: if the page loads auxiliary datasets (payees, journal list, timeline, etc.), mock them too; missing secondary endpoints can make a primary-page check look flaky.

Key lessons from this session
- Storage-only fake login can fail even when the keys are correct, because the app bootstrap may immediately fetch profile/permissions and clear invalid state.
- For auth-gated admin surfaces, a one-off deterministic Playwright harness is often faster and more trustworthy than repeated manual browser reinjection attempts.
- Mobile screenshots exposed a drawer width overflow bug that desktop checks did not catch; include at least one detail drawer/modal open state in 375px verification.
- When Playwright bundled browsers are unavailable, using system Chrome via `executablePath` is an acceptable fallback for local evidence generation.

Suggested artifact bundle
- `report.json`
- `desktop-*.png`
- `mobile-*.png`
- optional script path under project `.hermes/qa/`

Do not overclaim
- Do not call this full acceptance for auth, GA, permissions, backend contracts, or write actions.
- Do not let mocked API fixtures hide a backend-owned issue once the task scope requires real contract verification.

## Hard blocker: email+OTP auth flows

When the app uses email+OTP (or phone+OTP) login with no password, this mocked-auth pattern CANNOT work. The login flow is: email input → server sends OTP → user enters OTP → session created. There is no credential to seed into storage; the session token is only issued after a successful OTP exchange.

Options when blocked by email+OTP auth:
1. **Lark Mail OTP**: If the test mailbox is in Lark/Feishu Desktop, use `references/email-otp-lark-verification.md` to read the OTP via screencapture+OCR.
2. **Pre-seeded test token**: If the project Workpad documents a long-lived test token or refresh token, seed it directly. Check `.env.local` or Workpad for `UVISA_TEST_*` variables.
3. **Test-channel bypass**: Some backends have a dev-only OTP bypass (e.g. hardcoded code `000000` or a test endpoint). Check backend config/properties for `dev`, `test`, or `mock` profiles.
4. **Fallback to unit/integration evidence**: If none of the above are available, document the blocker and use unit tests + type-check + code diff as verification evidence. Do not claim browser-verified.
