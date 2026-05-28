# Project Workpad: test environments, test accounts, and auth/session debug channels

Use this reference when a user asks to add QA/test-environment facts into a project image, Workpad, or local-brain project note.

## Scope rule

- Store these facts in the project Workpad/local project note, not global memory.
- Do not copy test credentials, session tokens, cookies, OTP workflows, or debug-channel details into public README, PR descriptions, issues, or broad cross-project playbooks unless explicitly sanitized.
- If the user later says the account is not disposable/test-only, remove it from the Workpad and advise rotating credentials.

## What to store

Good Workpad fields:

- Environment name and URL.
- Test account identity fields needed for repeatable QA, e.g. phone/UID/KYC level.
- Stable test PIN/password only if explicitly provided for a disposable test account.
- Source and date, e.g. “user-provided for test environment”.
- Auth/session reuse rule: existing browser session, storageState/auth-state artifact, or project acceptance harness must be discovered and reused before creating any new login/debug flow.
- Verification rule: must be validated by browser/Playwright before claiming PASS.
- Evidence-deposition rule: login/console/network/storage proof belongs in evidence ledger/UI test ledger, with secrets redacted.

## Existing-capability discovery pattern

For login-gated UI验收, document and follow the discovery order rather than a one-off credential path:

1. Check current browser/browser-harness context for an already authenticated session.
2. Search the project for existing `storageState`, `auth-state`, real-session fixtures, or acceptance scripts.
3. Search session history / Workpad / project profile for the previously established login or acceptance harness.
4. Reuse the project’s existing Playwright/browser harness if one exists.
5. If no reusable capability exists, record a blocker such as `session_artifact_missing` or `auth_capability_missing`; do not invent a fresh debug script during ordinary UI验收.

## OTP/SMS debug-channel pattern

Only document or use a code-retrieval channel when the task explicitly validates auth/OTP/session behavior, or when the user explicitly asks to rerun the login contract.

- Store the method, not the one-time code value.
- Keep the method project-scoped and redact service/session details that reveal credentials.
- Use only the latest code matching the current request and target account.
- One-time OTP values must not be persisted in Workpad, screenshots committed to repo, public docs, PRs/issues, or global memory.

## Suggested Workpad wording

```md
### Auth/session reuse discovery / 线上登录能力发现

- 普通线上 UI 验收默认不重新触发 OTP，也不新写一次性登录脚本；先找并复用既有功能。
- 必查顺序：当前 browser/session → 项目 storageState/auth-state/acceptance 脚本 → 历史会话/Workpad → repo 既有 Playwright harness。
- 只有 auth/OTP/session 合约任务或用户明确要求重跑登录合约时，才进入登录挑战。
- 若无可复用能力，记录 `session_artifact_missing` / `auth_capability_missing`，不要临时改写流程。
```

## Verification after editing

- Search the Workpad for stale “OTP source / Deploy Logs / latest LOGIN code” requirements and either remove them or mark them historical-only.
- Run any project/local-brain self-check script if available.
- Confirm application repo status if only the brain/Workpad should change.
