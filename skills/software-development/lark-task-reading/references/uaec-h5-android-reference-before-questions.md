# UAEC H5 task intake: read Android reference before product questions

Applicability:
- UAEC H5 tasks where the Lark text asks H5 to “同步移动端/安卓端”, “参考安卓端”, “1:1还原”, or otherwise match the native app.
- Especially notification center, QR/scan login, partner/copartner, trading menu functions, and other parity work where `/Users/charles/Desktop/folder/work/uaec-android` is the explicit reference project.

Anti-conditions:
- Do not apply globally to unrelated projects.
- Do not treat Android as the edit target; it is read-only reference unless the user explicitly asks to modify Android.
- Do not ask the user broad questions that can be answered by reading Android source first. Ask only after source inspection leaves a real product ambiguity.

## Workflow:
1. Confirm the H5 task scope from Lark/task board, including section and assignee filter.
2. If Figma/design access is missing or unavailable, treat `uaec-android` as the authoritative visual/interaction fallback for UAEC H5 parity tasks: reproduce Android layout, spacing, icon assets, text hierarchy, and interaction flow as closely as H5/Vue/Vant allows. Do **not** stop just because Figma is unavailable. Android remains read-only reference; edit only `uaec-h5` unless explicitly directed otherwise.
3. Before asking product questions, search/read the Android reference repo for the matching domain:
   - Notification center: search/read `SystemMessageActivity`, message detail/settings screens, and `UrlContent` message constants.
   - QR/PC scan login: search/read scanner flow, `scanQrcode`, `qrcodeLogin`, `WEB_LOGIN`, and any confirmation dialog.
   - Partner/copartner: search/read `property/partner/Partner*` and `UrlContent` copartner/rebate/share constants.
   - Asset/coin visual parity: read Android XML layout(s), drawable assets, dimensions, colors, and adapter/activity code before changing H5 CSS/assets.
4. Extract concrete evidence: file paths, endpoint constants, request params, UI states, navigation flow, dimensions, drawable/icon names, and acceptance behavior.
5. Convert the task plan from “ask user what this means” to “Android says X; H5 needs Y; remaining ambiguity is Z”.
6. For visual parity patches, add a small contract test or static assertion that proves the H5 page uses the intended Android-derived asset/style token, then run build/diff checks.
7. Keep project-specific paths/evidence in the UAEC project profile or a scoped task plan. The skill should keep only this reusable intake rule.

Pitfall from session:
- Treating a task like “H5 通知中心新增小铃铛/扫码” as an open product question was wrong because Android already had implemented reference flows. The correct sequence is: read Android first, then ask narrower questions only if H5/browser constraints differ from native.

Observed Android reference anchors from UAEC session:
- Notification center: `app/src/main/java/com/uu/market/home/SystemMessageActivity.java`; endpoints `together/getNotifyTypes`, `together/getReceviceMsgListV1`, `together/updateReceiveInfoStateByIds`.
- QR login: `app/src/main/java/com/uu/market/home/FrontPageFragment.java`; `GET {WEB_LOGIN}/user/scanQrcode` with `qrcode`, then `POST {WEB_LOGIN}/user/qrcodeLogin` with `qrcode` and `userId`.
- Partner: `app/src/main/java/com/uu/market/property/partner/PartnerMainActivity.java` and sibling `Partner*` files; main endpoints include `copartner/findGroup`, `copartner/rebateDetail`, share interface, upgrade/rebate/team APIs.
