# H5 native-parity route contracts and Chrome/CDP smoke probes

Applicability: mobile H5/PWA work where a native Android/iOS screen is the reference and the H5 implementation must preserve native navigation semantics. This reference is class-level: examples use generic `BASE/QUOTE` placeholders, not project-specific symbols or URLs.

Anti-conditions:

- Do not store project-specific partner IDs, domains, branch names, API paths, tokens, screenshots, or evidence filenames here; put them in the project profile/SSOT.
- Do not use this as proof of device, PWA-installed, logged-in, production, or order-submission certification; it only describes local route/viewport smoke technique.

## Route-contract parity from native apps

Native navigation often carries separate semantic fields that should not be collapsed in H5 URLs:

- Display name, e.g. `tradeName=BASE/QUOTE`, belongs to visible title/split labels.
- Request/WS symbol, e.g. `symbol=basequote`, belongs to API and socket identity.
- Stable trade id, e.g. `tradeId` / `partnerTradeId`, belongs to collection/order/route identity.
- Direction, e.g. native `buyselltype=BUY|SELL`, may coexist with H5 `side=buy|sell`.
- Extra labels, e.g. `coinTagName`, should be passed through if the native flow uses them.

Procedure:

1. Read the native source for both sender and receiver. For Android, inspect `putExtra(...)`, `getStringExtra(...)`, broadcasts, and container sync methods.
2. Preserve native identity fields as separate URL params or typed route state in H5. Do not compact `BASE/QUOTE` into `BASEQUOTE` if the destination UI splits on `/`.
3. Make the H5 receiver accept both H5-native params and native-style params when both are plausible, e.g. `side=sell` and `buyselltype=SELL`.
4. If async lists have not loaded yet, use URL params as a temporary selected-entity fallback so the page does not visually regress to a default pair.
5. Verify route semantics by clicking through in mobile viewport and reading back URL params plus visible title/form state; do not rely on unitless code review.

Negative checks:

- Do not submit orders or mutate auth-gated state in anonymous/local parity smokes.
- Do not persist or print tokens/cookies from a logged-in browser.
- Do not claim device/PWA/auth certification from local Chrome viewport evidence.

## Chrome/CDP smoke probe target selection

When using raw Chrome DevTools Protocol for H5 smoke tests, never assume the first `/json` target is the page under test. Chrome may expose extension/background targets first.

Robust target selection:

1. Start Chrome with a fresh `--user-data-dir` and a known `--remote-debugging-port`.
2. Navigate an existing page target using `Page.navigate`, or explicitly select a target whose URL contains the expected local origin after navigation.
3. Reject `chrome-extension://`, `devtools://`, and background/service-worker targets for DOM probes.
4. Only run `Runtime.evaluate` after the selected target URL matches the expected origin/path.
5. If repeated smoke failures happen, split diagnostics: target URL -> body text -> selector/rect -> click -> post-click URL/readback.
6. Change the command signature after fixing the script so terminal guardrails do not treat it as the same repeated failure.

Minimal evidence packet:

- JSON with `ok`, pre-click and post-click readbacks, expected params, and negative flags.
- Mobile screenshot from the same run.
- Fresh scoped lint/build command outputs.
- SSOT path for evidence; do not write temporary smoke evidence into the product repo.
