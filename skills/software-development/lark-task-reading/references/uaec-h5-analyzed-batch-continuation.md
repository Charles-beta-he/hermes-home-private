# UAEC H5 analyzed-batch continuation pattern

Applicability:
- User asks to check UAEC H5 Lark tasks that were already analyzed, remaining work, or whether prior analysis/code work changed the remaining queue.
- Goal is read-only reconciliation of Lark live incomplete state, prior analysis artifacts, and code/MR evidence.

Anti-conditions:
- Do not close/write back Lark from this pattern alone; code-side merged evidence and Lark task lifecycle are separate gates.
- Do not treat stale `/tmp` artifacts as live state unless a fresh Lark auth/read has just proven the task still exists or the artifact is explicitly labeled historical.
- Do not mutate `uaec-android`; it is reference only unless explicitly requested.

Procedure:
1. Load `lark-task-reading` and `references/uaec-h5-live-task-inventory.md` first.
2. Use broad UAEC scope, never the UVISA default hard scope. For a quick freshness check, prefer the direct reader when comments/docs are not needed:
   ```bash
   python3 ~/.hermes/scripts/lark_oauth_guard.py --json --no-open
   python3 ~/.hermes/scripts/lark_task_reader.py --scope-mode off --no-comments --no-docs --summary
   ```
   If the unified `lark_task_flow.py --scope-mode off --no-docs --summary` times out or hits `IncompleteRead`, do not classify auth as broken if the OAuth guard says `valid_local_token`; fall back to the direct reader above for count/title freshness.
3. Recover prior analysis artifacts when present, especially:
   - `/tmp/uaec_h5_lark_category_robot_owned_10.md` — the analyzed 10 assignee tasks in the V1.2.0 H5 classification block.
   - `/tmp/uaec_h5_robot_owned_10_change_plan.md` — per-task implementation approach and risk split.
   - `/tmp/uaec_h5_mr73.json` — first-batch MR evidence when present.
4. Reconcile by GUID, not title only:
   - Start from the previously analyzed GUID set.
   - Subtract code-side merged/accepted GUIDs only when backed by MR/commit evidence.
   - Still report whether each GUID remains in the live Lark incomplete list; if it does, label it `code_done_but_lark_open` rather than done.
5. Keep the report split into three buckets:
   - `live_lark_open`: still returned by the fresh Lark read.
   - `code_side_done`: MR/commit evidence exists.
   - `implementation_remaining`: analyzed but not code-side done.
6. For the observed UAEC H5 analyzed batch shape, the first code-side batch may contain these five GUIDs (verify fresh each time before relying on it):
   - `fb3406dd-8c4a-40d4-b37a-a52601d15e05` banner routing/token handling.
   - `a44a3e2d-0360-4f81-92c5-ac16f8b5855d` invitation register logo no-navigation.
   - `d3b40d61-8543-44c7-882e-d19977d4fa7f` global font token.
   - `8d6a53a6-454c-4172-9e5a-50058cf3ccea` home typography weight.
   - `96142806-4e19-4f8f-8d7a-9bdd74376957` home list spacing/price alignment/change-cell width.
7. If those five are verified as code-side done, the analyzed-batch implementation remainder is typically:
   - `5eb1b6fa-8f36-418a-9973-cb4d4c32fe33` assets-page UI.
   - `96a31348-de7c-44d2-bc8e-969e5b1a560b` coin-selection list UI.
   - `3aa79ae5-5269-4740-bb74-6cd00e2931af` market page parity (favorite/all/main/RWA dynamic areas).
   - `d082c02e-8e83-4188-a029-3858cb50b3c4` notification center + QR login.
     - Continuation pitfall from batch3: do not assume this is absent in H5. First search for existing `MessageCenter`, `MessageDetail`, `getNotifyTypes`, `getReceviceMsgListV1`, `updateReceiveInfoStateByIds`, and `selectHasUnreadCount`; H5 may already have notification APIs/routes/pages. A safe first slice is home-top entries + login guard + unread-dot hookup + scan-login page/API wrappers, aligned to Android `UrlContent.SCANQRCODE=user/scanQrcode` and `QRCODELOGIN=user/qrcodeLogin`.
     - For QR login, avoid adding a heavy camera dependency as the first slice unless required. Prefer progressive support: native `BarcodeDetector` image upload when available, plus manual/pasted QR-content fallback; extract `qrcode`/`qrCode`/`code` query params from PC QR URLs before calling APIs.
     - Verification checklist: add a Node contract test that checks home entries, route registration, API endpoint strings, login guard, and Android-reference parity (`qrcode + userId` on confirm), then run that test with the existing UAEC H5 contract tests, `git diff --check`, and `yarn build`.
   - `dafd7cd0-1a81-489b-8215-a3e601c00bf5` contract calculator.
8. Smart routed multi-model review gate before push/MR:
   - Trigger this gate for any analyzed UAEC-H5 Lark task touching auth/login/QR, funds/assets/trading, backend-configured routing, Android parity, or >2 runtime files. Do not rely only on the implementing model's self-review.
   - Route by surface: `security/auth` reviewer for login/QR/token/funds; `logic/parity` reviewer for Android endpoint/flow equivalence and task boundary; `ui/compat` reviewer for rendered entry/layout/browser support when UI changed. Same-family reviewers are advisory; at least one independent reviewer or deterministic substitute must approve before calling the patch review-complete.
   - Required packet: reviewed commit SHA, `git diff origin/develop...HEAD -- <scoped files>`, Android reference evidence if parity is claimed, deterministic verification commands/results, known boundaries (for example no live-camera scan in the first QR-login slice).
   - Required artifact: write a short review receipt under `/tmp` or project evidence containing verdicts, accepted blockers/fixes, advisory-only notes, verified SHA, and commands run. If a model/provider is unavailable, label the result `degraded_not_certified` rather than silently counting it.
   - If any reviewer reports a concrete reproducible security/correctness issue, add or run a failing check where practical, patch, rerun deterministic verification, and rerun the routed review on the final diff.
9. Recommended continuation order after reconciliation:
   1. Assets/coin-list visual work (`5eb1b6fa`, `96a31348`) after confirming actual route/component and Figma target.
   2. Market page parity (`3aa79ae5`) with backend-configured area/API/socket evidence.
   3. High-risk new features (`d082c02e`, `dafd7cd0`) after Android-reference extraction and API smoke.

Reporting template:
- Freshness: command + count + token status.
- Prior-analysis artifacts read.
- Code/MR evidence found.
- Live Lark state vs code-side state split.
- Remaining implementation list with risk/order.

Pitfalls:
- A task can be merged in code and still remain Lark-open; do not flatten it to done.
- Local `develop` may be behind `origin/develop`; check remote merge evidence before saying code is missing.
- Lark task titles with “已改/已测” can still be incomplete; live incomplete state and closeout evidence are the source of truth.
