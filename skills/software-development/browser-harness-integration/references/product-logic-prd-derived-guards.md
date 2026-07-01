# Product Logic / PRD-derived Guards

Extracted from `/Users/charles/.hermes/skills/software-development/browser-harness-integration/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Product Logic / PRD-derived Guards

When a project has product/business semantics beyond page function (funds, KYC, registration boundaries, card lifecycle, allowed rails/networks, investment scope), use `references/prd-product-logic-guards.md`. Add deterministic Playwright tests that assert PRD invariants directly, run the configured browser matrix, and update the product ledger + UI ledger + Workpad. Treat single-surface coverage as PARTIAL, not PASS.

For frontend work that depends on a writable/runnable real backend, use `references/fullstack-real-backend-verification.md`: boot both repos, start real backend dependencies, curl exact service paths, run UI guards against the live stack, classify pre-existing backend-suite failures honestly, and commit frontend/backend scopes separately.

If a task changes both frontend and backend code, local full-stack browser evidence is mandatory for UI acceptance: start the local backend, point the local frontend at it, operate the browser walkthrough/regression yourself, score UI quality, and record console/network/storage/screenshots plus backend health/exact-service-path curl evidence. Mock-server and staging/Railway can be comparison or regression surfaces, but they do not substitute for local frontend → local backend acceptance of the changed contract.

For PRD/product-flow walkthroughs against a deployed/test backend, use `references/live-backend-product-flow-triage.md`: run the local frontend through the live backend, separate route reachability from true business closure, compare legacy vs canonical APIs, attribute abnormalities to frontend/backend/config/test-seed owners, and mark safe-but-unexecuted writes explicitly.

Regression coverage must be labeled by evidence level. Frontend unit/build and mock-server fixtures prove only frontend behavior and expected contract shape; they do not certify that the real backend endpoint is filled, safe, or semantically correct. For backend-owned semantics (auth/OTP/PIN/2FA/device/session/KYC/card/wallet/topup/exchange/remittance/notification/account/profile/money/status/time/order), inspect backend controller/service/entity/repository and, when the contract changes, collect local/live backend curl or Playwright evidence plus backend targeted test/compile evidence.
