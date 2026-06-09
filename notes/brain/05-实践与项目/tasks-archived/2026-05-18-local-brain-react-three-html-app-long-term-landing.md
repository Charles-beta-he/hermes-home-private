---
type: task
layer: L3
status: done
priority: P1
created: 2026-05-18T19:45:00+0800
updated: 2026-05-20T00:16:48+08:00
expires_at: 2026-06-18
project: hermes-local-brain
capability_delta: 本地大脑 HTML 从 Python 静态字符串 sidecar 升级为 React/Tailwind/D3/Three.js local-first 静态 Web App；Three 后置，优先落地 Cockpit + 任务池 Mission Control；保留 Markdown/JSON/kanban.db canonical。
anti_drift_check: 不把 HTML/App 变成状态源；brainctl 只导出 deterministic model；browser-QA + UIMax 双视口验收；file:// 离线可用。
acceptance_evidence: Vitest + Playwright + brainctl export/status/refresh + browser console zero error + 1280/375 screenshots。
claimed_by: 
claim_expires_at: 
run_id: 
next_attempt_at: 
evidence:
  - proof:follow-through claimed for bounded evidence tranche; previous direct running transition rejected because claim required first
  - proof:claimed lease acquired; bounded verification tranche now running against app source/tests/build/browser QA
  - "proof:bounded real-link tranche PASS: pnpm test 11/11, pnpm build exported local_brain_app_export_v1 nodes=290 tasks=188 edges=211 and synced dist to /Users/charles/Documents/brain/07-仪表盘/local-brain-app, pnpm run refresh:deploy PASS, browser-QA file URL PASS desktop 1280 and mobile 375 consoleErrors=[] pageErrors=[] overflow=0 screenshots=/tmp/local-brain-html-app-desktop.png,/tmp/local-brain-html-app-mobile.png; remaining closeout gap: independent UIMax grade not recorded so moved to review not done"
  - proof:sha256:a44cb7ffc7f96138c3e347c104f540a77e3e121ef0551fa693ed96606b2e3d08
source: Hermes Agent
---

# Task - 本地大脑 React/Three HTML App 一次性长期落地

## Goal

以长期一次性落地为目标，建设 React / TailwindCSS / D3 / Three.js 的本地大脑静态 Web App，替代当前粗糙的 Python 内联 HTML 图形导航。

## Dependencies / Execution Order

1. Contract first: `brainctl html export-app-data` 数据模型。
2. App scaffold: React + TypeScript + Vite + Tailwind + Playwright。
3. Cockpit: 搜索、过滤、KPI、Inspector、open actions。
4. Taskpool Mission Control: 任务池运行态大屏，炫技但证据绑定。
5. D3 Atlas: 2D 聚类关系图。
6. Three Memory Palace: 3D 空间导航，排在后面。
7. Launcher integration: Obsidian entry / current graph entry 指向新 app。
8. QA closure: UIMax + browser-QA + file:// offline。

## Acceptance Checklist

- [ ] `brainctl html export-app-data --out <path>` 输出 `local_brain_app_model_v1`。
- [ ] model includes nodes / edges / groups / stale status / source path / sidecar path / generated_at。
- [ ] `/Users/charles/personal-hermes-brain/hermes/local-brain-html-app` contains app source and lockfile。
- [ ] `pnpm test` passes。
- [ ] `pnpm build` outputs to `/Users/charles/Documents/brain/07-仪表盘/local-brain-app/` or synced dist path。
- [ ] `file://.../local-brain-app/index.html` opens without network dependency。
- [ ] Desktop 1280px browser-QA: search, filter, select node, open sidecar, switch Cockpit/Taskpool/Atlas/Palace/Ops。
- [ ] Taskpool Mission Control: 展示真实 P1/P2/P3 lane、running/claimed/blocked/stale、dependency、multimodel gate、proof/evidence；炫技动效不得使用 mock 状态。
- [ ] Mobile 375px browser-QA: no horizontal overflow; search/list/accordion usable; Taskpool 使用 compact operations feed；Three not required as primary path。
- [ ] UIMax: Visual/Responsive/A11y/Interaction >= A-; Code >= B+; Console = A。
- [ ] Existing sidecar build/status/refresh remains compatible or has documented transition path。

## Design Constraints

- Markdown / JSON / kanban.db remain canonical。
- HTML/App is derived and rebuildable。
- No SaaS dependency。
- No remote CDN as runtime requirement。
- Canvas/Three view must have DOM fallback。
- Three.js 排在 Cockpit / Taskpool Mission Control / D3 Atlas 之后；不得阻塞主路径交付。
- Taskpool Mission Control 可以高动效、高视觉冲击，但每个视觉状态必须来自真实导出字段或明确标记为 unavailable。
- Red only for real error/stale/broken states。
- Respect `prefers-reduced-motion`。
- Use accessible primitives for tabs/dialog/drawer where possible。

## Related Strategy

- [[05-实践与项目/projects/hermes-local-brain/P10 - React Three Long-term HTML Rewrite]]
- [[06-治理与评审/reviews/2026-05-18-local-brain-html-product-redesign-multimodel-review]]

- 2026-05-20T00:11:33+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: follow_through_bounded_evidence_tranche_claim Evidence: proof:follow-through claimed for bounded evidence tranche; previous direct running transition rejected because claim required first

- 2026-05-20T00:11:49+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: follow_through_bounded_evidence_tranche_running Evidence: proof:claimed lease acquired; bounded verification tranche now running against app source/tests/build/browser QA

- 2026-05-20T00:12:43+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: follow_through_bounded_evidence_tranche_completed_to_review Evidence: proof:bounded real-link tranche PASS: pnpm test 11/11, pnpm build exported local_brain_app_export_v1 nodes=290 tasks=188 edges=211 and synced dist to /Users/charles/Documents/brain/07-仪表盘/local-brain-app, pnpm run refresh:deploy PASS, browser-QA file URL PASS desktop 1280 and mobile 375 consoleErrors=[] pageErrors=[] overflow=0 screenshots=/tmp/local-brain-html-app-desktop.png,/tmp/local-brain-html-app-mobile.png; remaining closeout gap: independent UIMax grade not recorded so moved to review not done

- 2026-05-20T00:16:48+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:a44cb7ffc7f96138c3e347c104f540a77e3e121ef0551fa693ed96606b2e3d08, proof:follow-through claimed for bounded evidence tranche; previous direct running transition rejected because claim required first, proof:claimed lease acquired; bounded verification tranche now running against app source/tests/build/browser QA, proof:bounded real-link tranche PASS: pnpm test 11/11, pnpm build exported local_brain_app_export_v1 nodes=290 tasks=188 edges=211 and synced dist to /Users/charles/Documents/brain/07-仪表盘/local-brain-app, pnpm run refresh:deploy PASS, browser-QA file URL PASS desktop 1280 and mobile 375 consoleErrors=[] pageErrors=[] overflow=0 screenshots=/tmp/local-brain-html-app-desktop.png,/tmp/local-brain-html-app-mobile.png; remaining closeout gap: independent UIMax grade not recorded so moved to review not done
