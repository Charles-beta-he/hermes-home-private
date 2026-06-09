---
type: review
layer: L6
status: completed
created: 2026-05-18T19:39:42+0800
source: Hermes Agent browser-QA + UIMax + multimodel design review
project: hermes-local-brain
---

# 本地大脑 HTML 产品化重设计多模型评审

## Evidence Boundary

- 本评审针对本地大脑 HTML 派生展示层，不改变 canonical truth。
- canonical source 仍为 `/Users/charles/Documents/brain` 下 Markdown/JSON/kanban.db。
- 当前实现证据：`/Users/charles/.hermes/scripts/brainctl.py` 的 `html build|status|refresh|watch|graph`，其中 sidecar 渲染约 lines 714-1205；当前图形导航：`/Users/charles/Documents/brain/07-仪表盘/本地大脑图形导航.html`。
- browser-QA/UIMax 初审已打开 `file:///Users/charles/Documents/brain/07-仪表盘/本地大脑图形导航.html`，识别到 98 个可点击 HTML 入口，视觉问题主要集中在密度、层次、可读性、关系图表达、响应式和交互发现性。
- 多模型调用：`consult_models.py` T1 调用 gpt-5.5 / gemini-3.1-pro-preview / mimo-v2.5-pro，实际仅 Gemini 完成，gpt/mimo 超时，因此该轮为 `degraded_not_certified`；另尝试 DeepSeek/Claude，Claude fallback 因 Gemini quota 失败，DeepSeek CLI 只返回上一轮摘要。结论采用“工具证据 + Gemini 有效建议 + 本轮 browser-QA 视觉证据”的降级综合，不宣称完整多模型认证。
- 多模型 artifact：`/Users/charles/.hermes/tick-20260518-112208-331095-p76625-4d0d5f29-f4462f55/`。

## Problem Statement

当前 HTML 不是“设计差一点”，而是仍停留在“脚本生成索引页”的产品层级：

1. 侧重点是把 Markdown/manifest 数据直接画出来，而不是转译成可操作的信息架构。
2. 95+ 节点一次性铺开，视觉噪音远大于导航价值。
3. 大量红色/虚线/连线制造调试态和告警感。
4. 节点标题和路径混排，截断严重，用户需要解码文件名而非浏览知识。
5. 缺少搜索、筛选、聚焦、折叠、详情面板等导航控制。
6. 桌面固定 SVG lane 视图对 375px 手机明显不成立。

## Product Direction

目标不是“做炫酷 3D 大屏”，而是把本地大脑 HTML 从 derived sidecar 升级为 local-first cognitive dashboard：

- 控制台：回答“我最近在做什么、哪些项目/评审/任务需要关注”。
- 导航器：搜索、筛选、聚焦、打开 Markdown/HTML/Obsidian 跳转。
- 图谱：展示关系，但默认降噪，只在用户选中/悬停时显露相关边。
- 证据面板：每个节点显示 source、generated_at、dependencies、stale/fresh、反链。
- QA 可验证：每个交互有 data-testid/aria-label，可用 browser-QA 双视口回归。

## Technology Decision

| 技术 | 结论 | 职责边界 | 不做什么 |
|---|---|---|---|
| React | P1 接入 | 管理搜索、筛选、视图切换、选中节点、详情面板、交互状态 | 不把整个本地大脑变成必须服务端运行的 SPA；不迁移 canonical 数据 |
| TailwindCSS | MVP/P0 接入 | 建立统一 spacing/color/typography/responsive token，先解决“丑”和响应式 | 不依赖远程 CDN 作为唯一运行路径；生产应可本地 vendor/预构建 |
| D3 | P1/P2 接入 | 关系图 layout、force/sankey/tree/edge bundling、hover 高亮相关边 | 不用 D3 管理整个 DOM；与 React 分工明确 |
| Canvas | P2 可选 | 大量节点/边的高性能绘制，适合 500+ 节点或动态 pan/zoom | MVP 不需要；先用 SVG/HTML 卡片验证 UX |
| Three.js | 暂不接入 | 仅作为未来“记忆宫殿/空间漫游”实验 | 不进入主线导航；3D 不解决当前密度/可读性/搜索问题 |

关键决策：先 Tailwind + 信息架构 + browser-QA，后 React/D3；Three.js 暂缓。当前痛点是产品化与信息降噪，不是渲染能力不足。

## Target IA / UX

页面结构建议：

```text
Header
  本地大脑控制台 / 更新时间 / 返回 Obsidian / 打开 Markdown

Global Command Bar
  搜索文档、项目、评审…
  视图切换：总览 / 最近更新 / 项目 / 评审 / 图谱 / 断链
  过滤：状态、类型、目录、stale/fresh、更新时间

KPI Strip
  HTML入口 / 内部跳转 / stale / 项目 / 评审 / 断链

Main Shell
  Left: 分组/筛选/最近入口
  Center: 当前视图（图谱、列表、卡片、矩阵）
  Right: 选中节点详情（source、sidecar、dependencies、打开/复制路径）
```

视图策略：

- 桌面 1280px：三栏 dashboard shell + 图谱/列表可切换。
- 平板：左侧 filter 可收起，右侧 detail drawer。
- 手机 375px：默认搜索 + accordion/list，不显示复杂连线；图谱变为可选 secondary view。

## Implementation Roadmap

### P0 / MVP：不引入复杂构建，先把当前 HTML 从 C/D 拉到 B-

范围：仍由 `brainctl.py` 生成静态 HTML，但重构模板、样式和交互骨架。

1. 抽出 HTML 模板函数：layout/header/kpi/filter/node-card/detail-panel，避免长字符串内联堆叠。
2. 引入本地 `brain-html.css` 或 Tailwind standalone 预构建 CSS；保留 file:// 可用。
3. 重做视觉系统：深色低噪背景、弱网格、低饱和边框、红色仅用于错误/断链。
4. graph view 默认隐藏/弱化边；节点 hover/focus 时高亮相关边。
5. 节点卡片只显示标题 + 类型/日期；完整路径放 tooltip/detail panel。
6. 增加 search/filter/sort 的最小原生 JS，支持按标题/路径过滤。
7. 增加 `data-testid` 与 aria：`brain-search`, `view-tabs`, `node-card`, `node-open`, `detail-panel`。
8. 生成 `html qa` 或独立 Playwright 脚本，双视口验证：1280px / 375px。

验收：UIMax 视觉/响应式/交互/console 至少 B；A11y 不低于 B-；browser console 零 JS error。

### P1：React + D3 数据驱动导航 App，但仍是 derived static app

范围：新增一个本地静态 app 入口，而不是替换所有 sidecar。

1. `brainctl html export-model` 生成 `brain-html-model.json`（nodes/edges/groups/kpi/staleness）。
2. React 管理 UI 状态：搜索、过滤、视图切换、选中节点、drawer。
3. D3 只负责 layout/scale/edge paths/force/sankey，不接管 React DOM。
4. 支持全局图谱、最近更新、项目、评审、断链检查 5 个视图。
5. 本地 vendor 依赖：`static/vendor/react.production.min.js`、`react-dom`、`d3`，或用 pnpm 构建后输出纯静态 assets。
6. 保留 file:// 和 Obsidian 跳转；所有打开行为同时支持 sidecar link 与 canonical Markdown path。

验收：browser-QA 能点击搜索、切视图、选节点、打开 sidecar、校验 drawer 内容；移动端不出现横向溢出。

### P2：Canvas / 高密度图谱优化

触发条件：节点超过 300-500 或 SVG hover/scroll 卡顿。

1. Canvas/WebGL 只绘制 edges/large graph background，HTML/React 仍负责可访问交互层。
2. 引入 pan/zoom/minimap/聚类展开。
3. 使用 edge bundling / community clustering。
4. 做快照 visual-regression，避免“酷但不可用”。

### P3：Three.js 记忆宫殿实验（非主线）

只作为单独实验入口，例如 `本地大脑空间漫游实验.html`，不得成为默认导航。评估指标是“是否提升定位和回忆效率”，不是视觉震撼。

## UIMax / UIproMax Gate

| 维度 | 当前初判 | MVP 目标 | P1 目标 |
|---|---|---|---|
| Visual Design | C-/D+ | B | A- |
| Responsiveness | D | B | A- |
| Accessibility | C | B | A- |
| Code Quality | C- | B | B+ |
| Interaction | D+ | B | A- |
| Console Health | 未发现阻断，需脚本化 | A | A |

阻断门禁：

- P0：console error、无法点击核心入口、375px 横向溢出、关键按钮不可聚焦。
- P1：搜索/过滤/视图切换任一主流程不可用；selected node drawer 与实际 sidecar/source 不一致。
- P2：Canvas/图谱造成 a11y 退化或 file:// 不可用。

## Browser-QA Test Ledger

建议新增稳定脚本或 ledger：`/Users/charles/Documents/brain/06-治理与评审/reviews/local-brain-html-browser-qa-ledger.md`。

核心用例：

1. Desktop smoke：打开图形导航，确认 h1、KPI、至少 1 个 node-card、返回链接存在。
2. Desktop interaction：搜索 `uvisa`，列表收敛，点击 Workpad 节点，确认 href 指向对应 sidecar。
3. Desktop focus：Tab 能聚焦搜索、视图 tab、节点、打开按钮；focus ring 可见。
4. Desktop graph：hover/focus 节点时相关边/节点高亮，无关内容降噪。
5. Mobile 375：无横向溢出；默认列表/accordion 可用；搜索框首屏可见；复杂图谱不强制展示。
6. Detail drawer：选中节点显示 source、sidecar、group、dependencies、open canonical/open HTML。
7. Console：零 JS error / requestfailed；file:// 下不依赖远程网络。
8. Staleness：人工改一个 markdown 后 `brainctl html status` 能显示 stale_source，refresh 后恢复 fresh。

## Acceptance Evidence Commands

```bash
python3 ~/.hermes/scripts/brainctl.py --json html status
python3 ~/.hermes/scripts/brainctl.py --json html refresh
python3 ~/.hermes/scripts/brainctl.py --json html graph
python3 ~/.hermes/scripts/local_brain_html_refresh.py
```

后续如果新增 Node/React 构建：

```bash
pnpm test
pnpm build
pnpm exec playwright test tests/local-brain-html.spec.ts
```

## Final Recommendation

推荐路线：

1. 立即做 P0：Tailwind/设计 token + 原生 JS 搜索筛选 + 信息降噪 + 双视口 browser-QA。
2. 再做 P1：React + D3 的 static derived app，读取 `brain-html-model.json`，保持 Markdown/kanban.db canonical。
3. 暂不做 Three.js；Canvas 只在 SVG/D3 性能不够时接入。
4. 每轮改动必须跑 UIMax/browser-QA，评分不达标不算完成。

本质原则：不要用更重的技术掩盖信息架构问题。先把“文件索引”产品化为“认知导航控制台”，再加 D3/Canvas 增强图谱。
