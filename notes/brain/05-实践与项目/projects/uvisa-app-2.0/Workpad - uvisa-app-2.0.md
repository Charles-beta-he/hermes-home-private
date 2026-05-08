---
title: Workpad - uvisa-app-2.0
created: 2026-05-08
updated: 2026-05-08 16:20:00 CST
type: project_workpad
project: uvisa-app-2.0
repo_path: /Users/charles/Desktop/folder/work/uvisa-app-2.0
branch: feat/uvisa-2.0
head: 0bfe1b2
status: active_project_working_memory
multi_model_tick: /Users/charles/.hermes/tick-20260508-080122
truth_status: grounded
verified_claim_count: 5/5
---

# Workpad - uvisa-app-2.0

> 规则：这是项目工作记忆，不是全局 memory。跨项目规则进 playbook/skill；项目目标、红线、业务流、验收矩阵留在本文件。

## 0. 元信息

- Project: uvisa-app-2.0
- Path: `/Users/charles/Desktop/folder/work/uvisa-app-2.0`
- Branch: `feat/uvisa-2.0`
- HEAD: `0bfe1b2`
- Product type: 移动 H5 金融/银行卡/加密资产前端
- Stack: React 19 + Vite + TypeScript + Zustand + Tailwind + mock-server + Vitest + Playwright
- Current route count: 78
- Current screen count: 72
- Service files: 22
- Last verified: 2026-05-08 16:12:56 CST
- Current scope: 只落地 Project Workpad 与自检，不修改 app 代码。

## 1. North Star

让 `uvisa-app-2.0` 在不丢功能、不降精度、不破坏原字段展示与 H5 交互的前提下，持续对齐参考 `uvisa-app` 的功能完成度，达到 P10/A+ 前端上线级：功能完整、交互闭环、移动端可用、i18n/dark/PWA/观测/后端联调可验证。

决策更新（2026-05-08）：用户已确认直接以 `uvisa-app-2.0` 当前状态为主，不再等待旧 `uvisa-app` reference anchor。因此后续 loop 的基线是当前 repo 的代码、路由、screens、UI_TEST_CASES、ADR 与真实浏览器验收结果；旧 reference 仅作为历史候选材料，不能阻塞当前闭环推进。

## 2. Non-goals

- 本 Workpad 落地不修改 `/Users/charles/Desktop/folder/work/uvisa-app-2.0` 代码。
- 不把项目临时状态写入全局 persistent memory。
- 不用删除按钮、删除路由、隐藏字段、吞错来制造“无 dead UI”。
- 不在缺少 browser/Playwright 证据时宣称 UI 已 A+。
- 不把 README 模板文字当作产品事实；以代码、UI_TEST_CASES、ADR、会话画像和实测证据为准。

## 3. Anchors

| Anchor | Path/URL | Type | Immutable? | Verification |
|---|---|---|---|---|
| Current project | `/Users/charles/Desktop/folder/work/uvisa-app-2.0` | code repo | No | `git status`, package scripts, routes/screens |
| Current-state baseline | `/Users/charles/Desktop/folder/work/uvisa-app-2.0` | canonical baseline | Yes for next loop | 以当前 routes/screens/docs/tests 为主；本轮记录 78 routes / 72 screens |
| Historical reference candidate | `/Users/charles/Downloads/uvisa-app` | optional historical material | No | 仅作参考，不作为阻塞 gate |
| UI test ledger | `docs/UI_TEST_CASES.md` | project evidence | Append-only preferred | PASS/TODO/FAIL/BLOCK/SKIP 状态与证据 |
| ADR index | `docs/decisions/INDEX.md` | architecture evidence | Append-only preferred | ADR-001..008 |
| Project Claude profile | `/Users/charles/Documents/brain/01-系统与偏好/prefs/uvisa-app-2.0-Claude会话画像-2026-05-08.md` | work-habit evidence | Stable snapshot | multi-model tick 20260508-072835 |
| Frontend closure playbook | `/Users/charles/Documents/brain/05-实践与项目/实践方案/前端闭环验收标准.md` | cross-project standard | Stable evolving | browser/Playwright/evidence ledger |

## 4. Red Lines

- 不能通过删除功能、入口、展示字段、路由或按钮来修 dead UI；除非有证据证明该入口不属于当前业务范围，并写入 ADR/decision。
- 不能改坏原字段展示、原 H5 UI 行为、原业务语义。
- 不能只看截图正常就判定完成；必须验证入口、点击、反馈、状态、错误恢复、完成态。
- 不能用 mock 成功掩盖真实后端路径不一致；mock/real backend alignment 必须有证据。
- 不能跳过 i18n/dark/mobile/PWA/console/network 检查宣称 A+。
- 不能把本项目临时 TODO、当前进度、未验证猜测写进全局 memory。

## 5. Skill Route

| Task Type | Required Skills/Tools | Verification Gate |
|---|---|---|
| Read repo / restore context | source-driven-development, codebase-intelligence, project `.claude/skills/read-repo` | README/package/UI_TEST_CASES/ADR/routes/screens/services 摘要 |
| Architecture / goal shaping | p10, p9, multi-model-thinking | claims/evidence bundle；T2/T3 只在高风险/跨模块时启用 |
| Code edit | project `.claude/skills/modify-code`, test-driven-development, incremental-implementation | caller scan + lint/tsc/test/build |
| Frontend flow closure | react-architecture-migration, browser-harness-integration, visual-regression, uimax-audit | Playwright/browser-harness + console/network/storage |
| UI quality | ui-ux-pro-max, baseline-ui, fixing-accessibility, fixing-motion-performance | mobile 375/390, dark, i18n overflow, interaction feedback |
| Backend/mock alignment | react-architecture-migration Round 9.5, source-driven-development | service path ↔ mock server ↔ real API evidence |
| Documentation deposition | obsidian, documentation-and-adrs | UI_TEST_CASES / ADR / Workpad Evidence Ledger updated |
| Control-plane check | this self-check script | `python3 ~/.hermes/scripts/uvisa_app_2_workpad_selfcheck.py` PASS |

## 6. Business Flow Matrix

| Flow | Entry | Happy Path | Error Path | Finish State | Evidence |
|---|---|---|---|---|---|
| Auth / 启动 | /login, /verify, /pin-setup | 手机号/验证码/PIN -> /home | 错码、refresh 失败、退出登录 | 登录态明确；失败回 login；无 token 残留 | docs/UI_TEST_CASES.md AUTH-* |
| Home / Wallet / Tx | /home, /account/:ccy, /tx, /tx/:id | 资产、钱包、交易列表/详情可达 | 空交易、长地址、筛选无结果 | 列表/详情/通知回写一致 | HOME-*, TX-* |
| Card | /card, /card/cvv, /card/freeze, /card/topup, /card/withdraw, /card/limits, /card/pin | 卡详情、CVV、冻结、充值提现、限额/PIN | 弱 PIN、冻结后入口、防重复提交 | finish 或状态更新可见 | CARD-* |
| Topup | /topup, /topup/swift/*, /topup/usdt, /topup/cny/* | SWIFT/USDT/CNY 充值路径 | 轮询超时、hidden tab、网络失败 | progress/finish 可达，订单状态一致 | TOPUP-* |
| Exchange | /exchange, /exchange/confirm, /exchange/finish, /order/:id | quote -> confirm -> execute -> order | 报价过期、不支持币对、刷新失败 | 订单详情/timeline 可达 | EX-* |
| Remit | /remit, /remit/payees/*, /remit/:payeeId/* | 收款人 -> 金额 -> preview -> PIN/2FA -> finish | 删除收款人、2FA 错误、返回中断 | finish/timeline/收款人列表一致 | RMT-* |
| Payout | /payout, /payout/crypto/:asset, /payout/usdt, /payout/cny | 地址/收款账户 -> 提交 -> finish | 地址格式、网络选择、余额不足 | finish + tx 回写 | PAYOUT-* |
| Wealth | /wealth, /wealth/product/:id, /wealth/buy/*, /wealth/holdings, /wealth/holding/:id | 产品 -> 购买 -> PIN/2FA -> finish；持仓/赎回 | 金额边界、协议未勾选、赎回失败 | 持仓/收益/详情回写 | WLT-* |
| Me / Security / Customer / Legal | /me, /me/security/*, /me/customer, /legal/:slug | 安全中心、客服、语言/主题、about/legal | 换绑三段、2FA、支付/登录密码错误 | 保护页/设置页状态明确 | SMK-03..08, ME-* |
| Cross-cutting | i18n, dark, mobile, PWA, Sentry/web-vitals, mock/real API | 主题/语言/移动视口/更新提示/API 对齐 | 长英文溢出、dark 跟随失败、SW 旧缓存、API 404 | console/network 清洁，证据入账 | 前端闭环验收标准 + UI_TEST_CASES |

## 7. Acceptance Matrix

| Gate | Command/Tool | Pass Criteria | Last Result / Rule |
|---|---|---|---|
| Scope / no app-code change | `git status --short -- /Users/charles/Desktop/folder/work/uvisa-app-2.0` | 本轮仅 brain/scripts 变更，app repo 不被修改 | 本次 Workpad 落地不改 app 代码 |
| Lint | `eslint .` | eslint 无新增错误 | 下次代码 loop 必跑 |
| Build / TypeScript | `tsc -b && vite build` | tsc -b && vite build 通过；若已有 tsc 历史错误需记录隔离 | 下次代码 loop 必跑 |
| Unit | `vitest run` | vitest run 通过；新增逻辑需补回归 | 下次代码 loop 必跑 |
| E2E | `npx playwright test` | 关键 money-moving/auth/security 流程通过 | 下次 UI loop 必跑 |
| Browser-harness / Playwright manual | `browser-harness 或 Playwright + console/network` | 移动端 390/375 视口、dark/i18n、toast/dialog/返回中断有证据 | 下次 UI loop 必跑 |
| Mock / real backend alignment | `服务路径扫描 + mock-server route check + network panel` | service path 与 mock/真实 API 无未解释 404；真实后端切换不破坏 demo | 下次后端联调必跑 |
| Docs deposition | `更新 docs/UI_TEST_CASES.md / ADR / Workpad Evidence Ledger` | bug fix/架构选择/验收结果有证据路径 | 每轮结束必做 |
| Control-plane self-check | `python3 ~/.hermes/scripts/uvisa_app_2_workpad_selfcheck.py` | Workpad 可检索、结构完整、无明显 secret | 本次 PASS 后登记 |

## 8. Evidence Ledger

| Date | Claim | Evidence Path | Status | Expiry / Next Check |
|---|---|---|---|---|
| 2026-05-08 | Project has enough evidence for Workpad | `/tmp/uvisa_workpad_next/uvisa_workpad_mm_state.json`, `/Users/charles/.hermes/tick-20260508-080122` | grounded 5/5 | Refresh when routes/screens/scripts materially change |
| 2026-05-08 | Project has 78 routes and 72 screens | `/tmp/uvisa_workpad_next/evidence_requests_fulfilled.json` | verified | Re-run before parity diff |
| 2026-05-08 | UI test ledger exists and contains mixed status evidence | `docs/UI_TEST_CASES.md` | keyword_counts PASS=108, TODO=35, FAIL=7, BLOCK=1, SKIP=3 | Do not treat keyword counts as unique-test pass rate |
| 2026-05-08 | Red lines and workflow habits are grounded | `uvisa-app-2.0-Claude会话画像-2026-05-08.md` | grounded | Re-evaluate if user changes project goal |
| 2026-05-08 | Cross-project closure standard exists | `前端闭环验收标准.md` | verified | Reuse across frontend projects |
| 2026-05-08 | User decision: current-state baseline wins | current conversation decision | verified by user instruction | 后续以当前 uvisa-app-2.0 状态推进 |
| 2026-05-08 | Historical reference candidate exists | `/Users/charles/Downloads/uvisa-app` | non-blocking reference | 仅作历史对照，不作为当前验收 gate |

## 8.1 Claim / Evidence IDs

- Claims: C-001, C-002, C-003, C-004, C-005
- Evidence: E-001, E-002, E-003, E-004, E-005, E-006, E-007
- Source state: `/tmp/uvisa_workpad_next/uvisa_workpad_mm_state.json`
- Multi-model tick: `/Users/charles/.hermes/tick-20260508-080122`

## 9. Known Debts / Open Risks

| ID | Risk | Severity | Owner | Next Check |
|---|---|---|---|---|
| R-001 | 当前状态基线可能仍含历史 TODO/FAIL/BLOCK，不能因为不等旧参考就降低闭环标准 | 4 | next loop | 从 UI_TEST_CASES 和真实浏览器结果生成 P0/P1 队列 |
| R-002 | UI_TEST_CASES includes TODO/FAIL/BLOCK keyword counts; cannot claim A+ until actual current run evidence updates ledger | 4 | next loop | Run Playwright/browser-harness and update statuses |
| R-003 | Real backend vs mock alignment can drift as APIs change | 4 | next backend loop | service path scan + network check |
| R-004 | i18n/dark/mobile/PWA issues often pass build but fail real UI | 3 | UI loop | 375/390 viewport + system dark + language switch |
| R-005 | Long-running loop may drift from red lines if Workpad is not read at session start | 3 | agent | Load this Workpad before code changes |

## 10. Next Loop Queue

- [ ] Freeze current-state baseline: record current routes/screens/services/docs snapshot as next loop starting point.
- [ ] Build current-state closure backlog: derive P0/P1/P2 from UI_TEST_CASES TODO/FAIL/BLOCK + live browser evidence.
- [ ] Convert UI_TEST_CASES TODO/FAIL/BLOCK into prioritized P0/P1/P2 loop queue.
- [ ] Run deterministic gates: lint, build/tsc, vitest.
- [ ] Run Playwright/browser-harness mobile dark/i18n closure sweep.
- [ ] Run mock/real backend path alignment check and record unresolved API mismatches.
- [ ] Update docs/UI_TEST_CASES.md, ADR if needed, and this Evidence Ledger after each loop.

## 11. Deposition Rules

- Stable project convention → this Workpad or project `.claude/skills`.
- Cross-project workflow → `前端闭环验收标准.md` / skill.
- User durable preference → global memory only if still true across projects.
- Completed task status → session transcript/task log, not memory.
- Secrets/tokens/passwords/API keys → never copy into brain; use `[REDACTED]`.
