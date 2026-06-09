---
type: strategy
layer: L2
status: active
created: 2026-05-18T19:45:00+0800
project: hermes-local-brain
canonical_vault: /Users/charles/Documents/brain
source: Hermes Agent
---

# P10 - React / Three.js Long-term HTML Rewrite

## Decision

接受“长期一次性落地”路线：不再把本地大脑 HTML 视为 `brainctl.py` 里几段静态字符串的增强，而是建设一个长期维护的本地 Web App。

核心判断：

- React / Tailwind / D3 / Three.js 可以一上来进入主架构。
- 但 canonical truth 不迁移：Markdown / JSON / kanban.db 仍是唯一可信源。
- 新系统是 local-first derived UI：可重建、可审计、可 browser-QA、可 UIMax 评分。
- Three.js 排在后面：先完成 React/Tailwind cockpit 与任务池 Mission Control；3D 作为后续 Memory Palace / spatial view。
- “任务池相关”允许并且应该更炫技：这是本地大脑的运行态主战场，适合做 mission-control / command-center 风格，但必须保留可访问 DOM fallback 与真实状态证据。

## Target Architecture

```text
Canonical Layer
  /Users/charles/Documents/brain/**/*.md
  ~/.hermes/memory/html_sidecars.json
  kanban.db / taskpool state

Export Layer
  brainctl html export-app-data
    -> local-brain-model.json
    -> nodes / edges / groups / stale status / timestamps / source links

App Source Layer
  /Users/charles/personal-hermes-brain/hermes/local-brain-html-app
    React + TypeScript + Vite
    TailwindCSS
    D3 layout utilities
    Three.js / React Three Fiber
    Zustand or TanStack Store
    Playwright tests

Build Output Layer
  /Users/charles/Documents/brain/07-仪表盘/local-brain-app/
    index.html
    assets/*
    model snapshot or relative model loader

Entrypoints
  07-仪表盘/本地大脑HTML入口.md
  07-仪表盘/本地大脑图形导航.html -> redirect/link to local-brain-app/index.html
```

## Product Shape

### 1. Cockpit View - default

目标：替代当前“全量节点墙”。

- Header：本地大脑、更新时间、refresh 状态、返回 Obsidian、打开 canonical vault。
- Global Command：搜索文档/项目/评审/任务。
- KPI Strip：HTML 入口、stale、断链、项目、评审、任务、最近更新。
- Left Rail：视图切换与过滤器。
- Main：列表/卡片/矩阵/2D graph。
- Right Inspector：选中节点详情、source、sidecar、dependencies、open actions。

### 2. Atlas View - D3 2D graph

目标：可理解的关系导航，而不是蜘蛛网。

- D3 负责 layout / clustering / scales / edge path。
- React 负责节点组件、状态、详情面板。
- 默认隐藏弱关系；hover/focus/selected 后只高亮相关边。
- 支持 group collapse、time filter、type filter、path prefix filter。

### 3. Memory Palace View - Three.js

目标：利用空间记忆，而不是炫技。

- React Three Fiber + drei。
- 节点聚类为“星系/楼层/房间”：仪表盘、项目、治理评审、任务、知识原子。
- 相机移动必须有明确导航语义：搜索命中 -> fly-to cluster；选中节点 -> inspector。
- 3D 视图默认可关闭，`prefers-reduced-motion` 下禁用自动飞行。
- 所有核心打开操作必须有 DOM 可访问替代，不让 canvas 成为唯一入口。

### 4. Taskpool Mission Control - flashy but evidence-bound

目标：任务池相关需要“炫技”，但炫技服务于调度态势感知，不是装饰。

- 主视觉：mission-control command center，展示 P1/P2/P3 lane、running/claimed/blocked、dependency chain、autorun tick、multimodel gate、proof/evidence 状态。
- 可视化：animated lane flow、radar/pulse、dependency arcs、blocked heatmap、agent worker cards、timeline replay。
- 交互：点击任务打开 inspector；hover 展示证据摘要；filter by priority/lane/status/assignee；一键复制 task path / open canonical Markdown。
- 状态色：红色只用于 blocked/error/stale；高亮动效只表达真实运行态，例如 running pulse、claimed glow、blocked alarm。
- 降级：`prefers-reduced-motion` 下关闭 pulse/fly/loop；375px 使用 compact operations feed，而不是强塞大屏图。
- 证据边界：Mission Control 读取 taskpool/brain model，不直接写状态；任何 claim/transition 仍走既有 taskpool control plane 与 proof gate。

### 5. Ops / QA View

目标：给 Hermes 自己和 browser-QA 使用。

- stale/missing_source/missing_sidecar 列表。
- 断链检查。
- refresh/build 命令提示。
- UIMax 评分摘要。
- 最近 browser-QA 证据入口。

## Stack Decision

| Layer | Choice | Reason |
|---|---|---|
| Framework | React + TypeScript + Vite | 长期维护、构建静态输出、适合复杂交互 |
| Styling | TailwindCSS + CSS variables | 快速统一视觉系统，支持主题 token |
| State | Zustand or TanStack Store | 轻量管理 filter/search/selection/view state |
| 2D graph | D3 utilities | layout/math/scale 强，不接管 UI DOM |
| 3D graph | Three.js + React Three Fiber | React 内统一状态，减少 imperative 3D 孤岛 |
| Components | Base UI / React Aria primitives | 键盘、focus、dialog、tabs 不手写 |
| Tests | Vitest + Playwright | 数据转换单测 + browser-QA 双视口交互证据 |
| Build target | static file:// friendly | 本地大脑必须离线可用 |

## Implementation Phases

### Phase 0 - Contract-first scaffolding

TDD 先行，先写数据契约和测试，不先写漂亮 UI。

Deliverables:

- `brainctl html export-app-data --out ...`
- JSON schema: `local_brain_app_model_v1`
- App scaffold: React/Vite/Tailwind/TS/Playwright
- Fixture model tests
- Build output path under vault

Acceptance:

- Export JSON contains nodes/edges/groups/stale status/open targets.
- `pnpm test` passes.
- `pnpm build` outputs static app.
- `file://.../local-brain-app/index.html` opens without network dependency.

### Phase 1 - Cockpit MVP

Deliverables:

- Header + KPI strip + search + filters + list/cards + inspector。
- Core open actions：open HTML sidecar、open canonical Markdown、copy path。
- 1280px/375px responsive shell。

Acceptance:

- Search `uvisa` filters visible items。
- Select node opens inspector。
- 375px no horizontal overflow。
- Keyboard tab order works。
- Console zero error。

### Phase 2 - Taskpool Mission Control

Deliverables:

- Command-center 任务池运行态大屏。
- Priority lanes：P1/P2/P3/evolution/advisory。
- Status telemetry：running / claimed / blocked / ready / done / stale claim。
- Dependency arcs + proof/evidence badges + multimodel gate badges。
- Task inspector：canonical path、status、blocker、evidence、open actions。
- Motion profile：flashy default, reduced-motion safe。

Acceptance:

- 能从真实导出模型展示任务池状态，不使用 mock 状态冒充。
- 点击任一任务打开 inspector，并可跳转 canonical Markdown/HTML sidecar。
- blocked / stale / running 有明确但不误导的视觉区分。
- 375px 显示 compact operations feed，无横向溢出。
- Browser-QA 可验证 search/filter/select/open，不依赖只看 canvas。

### Phase 3 - D3 Atlas

Deliverables:

- 2D clustered graph。
- Hover/focus/selection relation highlighting。
- Group collapse and edge filtering。

Acceptance:

- Dense graph remains readable。
- Hover one node highlights related neighbors only。
- Graph interactions do not break list/search/inspector。

### Phase 4 - Three Memory Palace

Deliverables:

- 3D spatial graph with semantic clusters。
- Search result fly-to。
- Selected node syncs inspector。
- Reduced-motion fallback。

Acceptance:

- Canvas is not the only interaction path。
- `prefers-reduced-motion` disables camera animation。
- Browser-QA can still operate DOM controls。
- Performance acceptable at current 96 nodes and designed for 500+ nodes。

### Phase 5 - Replace legacy graph entrance

Deliverables:

- `brainctl html graph` writes launcher that points to React app。
- Existing sidecar HTML remains available for direct file reading。
- Cron refresh builds/export model safely。

Acceptance:

- `brainctl html status` remains fresh。
- `local_brain_html_refresh.py` refreshes model/app launcher。
- Obsidian entry opens new app。

## Browser-QA Gates

Required matrix:

| Viewport | Required |
|---|---|
| Desktop 1280x800 | cockpit, atlas, inspector, search, open sidecar |
| Mobile 375x812 | cockpit list/search/accordion, no horizontal overflow |
| Reduced motion | no auto fly/looping animation |
| file:// mode | no remote JS/CSS dependency |

Core tests:

1. App loads and shows KPI.
2. Search filters nodes.
3. View tabs switch Cockpit / Taskpool / Atlas / Palace / Ops.
4. Selecting node updates inspector.
5. Opening sidecar href is valid relative file path.
6. Mobile shell has no horizontal overflow.
7. Console has zero JS errors.
8. Three canvas is present only in Palace view and has DOM fallback controls.

## UIMax Target

Long-term one-shot landing target is not merely B; target A- minimum.

| Dimension | Gate |
|---|---|
| Visual Design | A- |
| Responsiveness | A- |
| Accessibility | A- |
| Code Quality | B+ |
| Interaction | A- |
| Console Health | A |

Hard blockers:

- file:// cannot load app。
- canonical Markdown path unavailable。
- 375px horizontal overflow。
- keyboard cannot reach search/view tabs/inspector open actions。
- Three.js view has no DOM fallback。
- HTML becomes canonical or writes task state directly。

## Key Risks and Mitigations

| Risk | Mitigation |
|---|---|
| React app build complexity breaks local-first simplicity | Keep generated static build under vault; export model is deterministic |
| Three.js becomes visual gimmick | Put Three after Cockpit/Taskpool/D3; Palace view must satisfy search/fly-to/inspector tasks before default exposure |
| Taskpool “炫技” becomes fake telemetry | Every flashy state must be backed by exported taskpool status/proof fields; no mock running/blocked visuals in production |
| Canvas/WebGL hurts accessibility | DOM cockpit/list/inspector remains first-class; canvas never sole navigation |
| Dependency drift | Pin package versions; commit lockfile under personal-hermes-brain |
| brainctl bloats further | Move app source out of brainctl; brainctl only exports data and launches/builds |
| Browser-QA cannot inspect canvas internals | Test DOM controls + inspector state + canvas presence/perf, not raw pixels only |

## Recommended Immediate Next Step

Start Phase 0 as a real implementation task:

1. Add data export contract to `brainctl.py` via TDD.
2. Create `/Users/charles/personal-hermes-brain/hermes/local-brain-html-app` React/Vite/Tailwind/TS scaffold.
3. Add Vitest tests for model adapter.
4. Add Playwright smoke for built file:// app.
5. Build Cockpit UI first, then Taskpool Mission Control. Three.js waits until taskpool/status surfaces are useful and testable.

This is the correct architecture if the goal is “长期一次性落地”，而不是在 current HTML 字符串上继续 patch。
