# UAEC H5 live Lark task inventory

Applicability:
- User asks to inspect/check/list UAEC H5 Lark pending tasks or “我的 lark 任务待完成任务”.
- The goal is a read-only inventory or triage snapshot, not implementation or Lark writeback.

Anti-conditions:
- Do not use the UVISA default preferred scope as a hard filter for UAEC H5; it will hide UAEC tasks.
- Do not mutate Lark tasks, taskpool, or project repos during inventory unless the user explicitly asks to import/execute/close tasks.
- Do not treat Android as an edit target; it is only reference for parity tasks.

Procedure:
1. Load `lark-task-reading` and this UAEC reference before acting.
2. Read `/Users/charles/.hermes/project-profiles/uaec-h5.json` for canonical H5 and Android paths, source weighting, and verification ladder.
3. Run a live read with broad scope, not UVISA scope:
   ```bash
   python3 ~/.hermes/scripts/lark_task_flow.py --scope-mode off --no-docs --summary
   ```
   For machine-readable processing, save JSON:
   ```bash
   python3 ~/.hermes/scripts/lark_task_flow.py --scope-mode off --no-docs > /tmp/uaec_h5_lark_incomplete_tasks.json
   ```
4. Prove current user identity through `/authen/v1/user_info` using the same Lark user token, then filter ownership by `members[].role == "assignee"` and exact current-user `open_id`. Do not count follower-only membership as “my task”.
5. Check repo state for context only:
   ```bash
   git -C /Users/charles/Desktop/folder/work/uaec-h5 status --short --branch
   git -C /Users/charles/Desktop/folder/work/uaec-h5 log -1 --oneline --decorate
   git -C /Users/charles/Desktop/folder/work/uaec-android status --short --branch
   git -C /Users/charles/Desktop/folder/work/uaec-android log -1 --oneline --decorate
   ```
6. Produce a concise inventory report with:
   - live-read freshness and current Lark user;
   - total incomplete tasks assigned to the user;
   - tasklist distribution;
   - priority/category counts;
   - top tasks in Lark order with title + guid;
   - paths to saved JSON/Markdown artifacts if created.
7. If a task says “参考安卓端/同步移动端/三端”, classify it as Android-reference-needed and use `references/uaec-h5-android-reference-before-questions.md` before asking broad product questions.

Suggested UAEC triage buckets:
- P0 transaction/funds/assets correctness: spot/contract order, order book, precision, transfer, assets, balance, equivalents, deposit/withdrawal, fund flow, sockets.
- P0 login/register/security/risk: login, register, password, OTP/email/SMS, captcha, account kickout, security center, Google auth, biometric/passkey, regional/IP blocking.
- P1 large feature/mobile parity: notification center, QR login, partner/copartner, market page, three-end home/recharge revamps, diamond-grid features, GitBook/help center.
- P1 PWA/cache/performance: PWA logo/cache/update, standalone chrome colors, reconnect, U-card jank.
- P1 visual/interaction/i18n: Figma 1:1, list spacing, icons, underline, typography, language/i18n, banner/logo navigation.
- P2 support/solution-needed: test support, cross-team API/config negotiation, x-domain/merchant config discussions.

Pitfalls:
- The default Lark reader scope prefers `UVISA-2.0新版开发`; for UAEC use `--scope-mode off` unless a UAEC tasklist scope is explicitly configured.
- Lark task payloads may omit tasklist names for many items; absence of tasklist name does not mean the task is unrelated.
- Node version reported by the live shell may not match UAEC project expectations; inventory can note it, but do not claim build readiness until the project’s Node/Yarn version is verified for the actual build.
- Do not classify task completion from title suffixes like “已改/已测”; the live incomplete list plus ownership filter is the inventory source of truth.
