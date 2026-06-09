# PRD Compliance Audit Patterns

Recurring anti-patterns found when cross-referencing frontend code changes against PRD/product docs (UI_TEST_CASES.md, PRODUCT_USER_LOGIC_TEST_CASES.md).

## Anti-Pattern 1: Input-Level vs Submit-Level Validation Gap

**Signal**: PRD says "frontend form intercepts X" (e.g., IBAN format, phone number, amount range). Code change relaxes the input `onChange` handler (removes regex filter, auto-uppercase, character restriction) but the submit handler still calls a validator function.

**Why it matters**: The PRD requirement is about **user experience**, not just data integrity. "Frontend form intercepts" means the user should be guided/corrected during input, not surprised at submit time.

**Audit checklist**:
1. Read the `onChange` handler on the input field — what characters/formats does it enforce in real-time?
2. Read the submit/validation function — what does it reject?
3. If onChange is relaxed but submit is strict, the UX degraded from "auto-correct" to "submit error". Flag as PRD interaction regression even if data integrity is preserved.

**Example** (UVISA RemitNewSwiftScreen IBAN):
- Before: `v.toUpperCase().replace(/[^A-Z0-9]/g, "")` — auto-uppercases, filters invalid chars during typing
- After: `v.slice(0, 34)` — only limits length, allows any character
- Submit: `validateSwiftAccountNumber(acct)` still enforces A-Z+0-9, 6-34 chars
- Result: User types lowercase → gets error on submit instead of auto-correction. PRD RMT-01 says "前端表单拦截" — technically met at submit, but UX degraded.

**Fix pattern**: Keep `.slice()` for length limit (good UX for paste), add `.toUpperCase()` for auto-correction, keep submit validator as safety net.

## Anti-Pattern 2: Service-Layer Field Read But UI Not Enforcing

**Signal**: Backend API returns a field (e.g., `maxAmount`, `dailyLimit`, `rateLimit`). Frontend service layer parses and stores it. But the UI screen never reads it for validation/display.

**Why it matters**: The field exists in the data model, the service layer invests in parsing it, but the user gets no feedback. This creates a silent gap where the backend enforces limits the frontend doesn't preview.

**Audit checklist**1. Check `service.ts` interface — what fields are typed?
2. Check `service.ts` parse/normalize — which fields are extracted from API response?
3. Check the screen component — which of those fields are actually used for validation, display, or error messages?
4. Any field parsed but not consumed in the UI = potential gap.

**Example** (UVISA ExchangeScreen maxAmount):
- `exchange.service.ts` types `minAmount?: number; maxAmount?: number`
- `getEffectiveRate()` parses both from API response
- `ExchangeScreen` uses `minAmount` for "below minimum" validation
- `maxAmount` is never referenced in the screen → no "above maximum" error shown

**Fix pattern**: Add `aboveMax` validation parallel to `belowMin`, add i18n error key, disable CTA when over limit.

## Anti-Pattern 3: Language Detection for Error Localization

**Signal**: Backend returns error messages in mixed languages (sometimes Chinese, sometimes English, sometimes backend codes). Frontend needs to show user-friendly messages.

**Pattern**: Use `navigator.language` to detect UI language, then:
- If UI is Chinese + message is pure ASCII → likely a backend code/English error → replace with Chinese generic message
- If UI is English + message contains CJK → likely a Chinese backend error → replace with English generic message
- Otherwise → pass through (correct language already)

**Why it works**: Backend error messages are unpredictable in language. The pure-ASCII / CJK heuristic catches backend codes and wrong-language messages without needing a whitelist.

**Caveat**: This will also filter legitimate ASCII business messages in Chinese UI (e.g., "KYC_LEVEL_INSUFFICIENT"). This is usually desired (those are technical codes, not user messages), but verify against the specific backend's error contract.

## Audit Workflow for Code Changes vs PRD

1. **git diff** the changed files
2. **Map each change to PRD constraints** — read PRODUCT_USER_LOGIC_TEST_CASES.md section headers, then UI_TEST_CASES.md relevant section
3. **Check input-level AND submit-level** for any form validation change
4. **Check service-layer fields** — are new typed fields actually consumed in UI?
5. **Check i18n keys** — new error states need corresponding i18n entries in both zh.json and en.json
6. **Report**: For each finding, state PRD requirement ID, before/after code, and whether it's a regression, gap, or pass

## Anti-Pattern 4: Input Collected But Never Submitted (Dead Feature)

**Signal**: UI adds an input field (text input, toggle, selector) that collects user data into local state. The data is passed via URL params or route state to the next screen. But the finish/submit screen never reads that param, and the service-layer submit payload has no field for it.

**Why it matters**: Users see the input, type something, and believe it was sent. The data silently disappears. This is worse than not having the field at all — it creates a false expectation.

**Audit checklist**:
1. For any new input field in a preview/confirm screen, trace the data flow forward:
   - Does the screen pass it to the next screen (URL param, route state, store)?
   - Does the finish/submit screen read it (`params.get("X")`, `location.state.X`)?
   - Does the service-layer `submit()` payload include it?
   - Does the API body construction send it (`body.fieldName = ...`)?
2. If any link in the chain is missing, the feature is dead.

**Example** (UVISA RemitPreviewScreen note/附言):
- `RemitPreviewScreen` adds `const [note, setNote] = useState("")` with UI input
- Passes via URL: `if (note) params.set("note", note)` → navigates to `/remit/finish?...&note=...`
- `RemitFinishScreen` never calls `params.get("note")`
- `RemitSubmitPayload` interface has no `note` field
- `remitService.submit()` body construction omits note
- Result: User types an附言, believes it's sent to recipient. Data is silently dropped.

**Fix pattern**: Either complete the chain (read param → include in payload → send to backend) or remove the input field to avoid misleading users. If backend doesn't support the field yet, don't add the UI.

**Pitfall — incomplete initial fix**: When fixing a dead feature, the first commit often addresses the most obvious gap (e.g., adding `note` to `RemitSubmitPayload` interface) but misses a downstream link (e.g., reading `note` from URL params in the finish screen). After fixing, re-run the full audit checklist end-to-end before committing. A follow-up commit for the same feature is a signal that the initial audit was incomplete — verify every link in the chain in a single pass.

## Anti-Pattern 5: Frontend Status Code That Backend Never Produces

**Signal**: Frontend adds a new status value to the `TxStatus` union type and implements display logic (color, icon, label). But the backend-to-frontend normalizer (`payoutStatusToTxStatus`, `transaction.service` status mapper) never maps any backend status to this new value.

**Why it matters**: The status is dead code — it has display logic but no data path. Tests may cover the display branch but can never exercise it through real data flow. This creates a false sense of feature completeness.

**Audit checklist**:
1. For any new status in a union type, check every normalizer/adapter that maps backend statuses to frontend statuses.
2. Verify at least one backend status maps to the new frontend status.
3. If the backend status doesn't exist yet, this is a forward-compatibility stub — document it as such and add a backend task.

**Example** (UVISA TxStatus "expired"):
- `types/index.ts` adds `"expired"` to `TxStatus` union
- `TransactionRow.tsx` renders expired with danger color + strikethrough
- `transaction.service.ts:83` maps backend `expired` → `failed` (not `expired`)
- `payoutStatusToTxStatus` has no case for `expired`
- Result: `expired` display logic is unreachable dead code.

**Fix pattern**: If backend will support it, keep the type but add a comment marking it as forward-compatible. If not, remove from the union and handle in the normalizer as `failed`.

## Anti-Pattern 6: Hardcoded Polling Interval vs Backend Semantic Value

**Signal**: A countdown timer or refresh mechanism uses a hardcoded constant (e.g., `FX_REFRESH_SECONDS = 30`). The backend provides a semantic value (e.g., `expiresAt`, `validFor`) that would make the countdown accurate.

**Why it matters**: The hardcoded interval is functionally safe (it refreshes often enough), but the UX countdown doesn't reflect actual backend state. If the backend validity period changes, the frontend won't adapt.

**Audit checklist**:
1. Is the countdown tied to a backend-provided expiry? Check for `expiresAt`, `validUntil`, `ttl` in the API response.
2. Does the frontend use the backend value, or a hardcoded constant?
3. If hardcoded: does the refresh mechanism (fetch new data on zero) compensate for the inaccuracy?

**Example** (UVISA CardWithdrawScreen FX countdown):
- `FX_REFRESH_SECONDS = 30` hardcoded
- Exchange flow uses `expiresAt` from quote response for accurate countdown
- Card withdraw FX uses the hardcoded 30s as a polling interval, not a quote expiry
- On zero, calls `fetchFxRates()` which gets a fresh rate
- Result: Functionally safe (always gets fresh rate), but countdown doesn't reflect actual rate validity. If backend rate validity is 60s, the UI refreshes too often; if 15s, the UI shows stale rates for 15s.

**Fix pattern**: Use backend `expiresAt` when available (like the exchange flow does). If no semantic value exists, document the constant as a "polling interval" not an "expiry countdown", and ensure the submit handler re-validates.

## Anti-Pattern 7: Feature Gate Default-Open on Error

**Signal**: A feature gate hook (checking platform config, feature flags, or remote config) uses `failOpenOnError = true` as default. When the config API is unreachable, the gate allows access.

**Why it matters**: This is usually intentional (preserve existing behavior when config is down), but it means a backend misconfiguration can't disable the feature. If the config API returns an error, users still see the feature.

**Audit checklist**:
1. What is the default behavior when the gate fails open? Is it safe?
2. Is there a way for ops to disable the feature if needed (e.g., returning a specific error code)?
3. Document the fail-open decision so future devs don't change it without understanding the tradeoff.

**Example** (UVISA useDomesticCnyTransferGate):
- `failOpenOnError = true` (default) means CNY transfer is allowed when config API fails
- Original PayoutCnyScreen also had this behavior (catch → default to true)
- If backend needs to disable CNY transfer, it must return a successful response with `domesticCnyTransferEnabled: false` — an error response won't block it

## Audit Workflow for Code Changes vs PRD (Extended)

7. **Trace new input fields end-to-end**: input → next screen param → finish screen read → service submit → API body. Any break = dead feature.
8. **Verify new status values have data paths**: union type → normalizer → at least one backend status maps to it.
9. **Check countdown/timer sources**: hardcoded constant vs backend semantic value. Document which is used.
10. **Audit feature gate fail behavior**: failOpen vs failClosed, and whether the default is documented.
