---
name: animation-system-optimization
description: "动效系统优化流程 — P10 审查驱动的迭代改进模式。参考 Lusion.co 实现方案，使用 P10→P9→P8 三层架构持续审查直到无改进。触发条件：'动效优化', 'animation review', 'P10 审查', 'until no issues'."
---

# 动效系统优化 — P10 审查驱动迭代模式

> 参考 Lusion.co 动效方案，使用三层架构 (P10→P9→P8) 持续优化直到 P10 找不到问题。

## 触发条件

用户说：`/pua loop "动效优化"` 或 `P10 审查` 或 `直到无改进`

## 核心流程

### Phase 0: Lusion.co 基准分析

先分析 Lusion.co (或类似高端动效网站) 的实现方案：

| 技术维度 | Lusion.co 方案 |
|---------|---------------|
| 渲染引擎 | Three.js (WebGL 2.0) |
| 动画驱动 | requestAnimationFrame + CSS Transitions |
| 缓动曲线 | cubic-bezier 预设库 |
| 滚动动画 | IntersectionObserver |
| 性能优化 | GPU 加速 (translateZ, will-change) |
| 3D 场景 | Canvas 分离 (主场景 + 过渡层) |

### Phase 1: 动效工具库搭建

创建 `lib/animations.js`：

```javascript
// 缓动曲线预设 (参考 Lusion.co)
export const easings = {
  bounce: 'cubic-bezier(0.34, 1.56, 0.64, 1)',      // 落子弹跳
  smoothIn: 'cubic-bezier(0.4, 0, 0.2, 1)',         // 平滑进入
  smoothOut: 'cubic-bezier(0, 0, 0.2, 1)',          // 平滑退出
  elastic: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)', // 弹性
  snappy: 'cubic-bezier(0.2, 0, 0, 1)',             // 快速响应
}

// RAF 驱动动画 (必须返回取消函数)
export function animate({ from, to, duration, easing, onUpdate, onComplete }) {
  let rafId = null
  // ... 实现
  return () => cancelAnimationFrame(rafId)
}

// 粒子效果 (必须返回清理函数，防止内存泄漏)
export function createParticles(container, options) {
  // ... 实现
  return () => { /* 清理 DOM + setTimeout */ }
}

// Canvas 动画辅助
export const canvasAnimations = {
  drawStone(ctx, x, y, radius, color, progress = 1) { },
  drawWinningLine(ctx, points, progress = 1) { },
}
```

### Phase 2: CSS 动效增强

在 `index.css` 添加关键帧和工具类：

```css
/* 核心动画 */
@keyframes stone-drop { /* 缩放弹跳 */ }
@keyframes stone-ripple { /* 涟漪扩散 */ }
@keyframes card-enter { /* 卡片入场 */ }
@keyframes thinking-dot { /* AI 思考 */ }

/* 工具类 */
.animate-stone-drop { animation: stone-drop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.transition-smooth { transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.gpu-accelerated { will-change: transform; transform: translateZ(0); }

/* 无障碍 (必须) */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Phase 3: P10 审查 + UI 走查 双轨迭代

使用 P10→P9→P8 三层架构 + 独立 UI 走查持续审查：

```
┌─────────────────────────────────────────────────────┐
│  P10 (CTO)                                          │
│  ├─ 定战略: 确定优化方向和优先级                     │
│  ├─ 造土壤: 建立质量门禁和基础设施                   │
│  └─ 断事用人: 做减法决策                            │
├─────────────────────────────────────────────────────┤
│  P9 (Tech Lead)                                     │
│  ├─ 拆解 Task Prompt (六要素)                        │
│  ├─ 文件域隔离                                       │
│  └─ 验收闭环                                        │
├─────────────────────────────────────────────────────┤
│  P8 (执行者)                                        │
│  └─ 具体代码实现                                    │
└─────────────────────────────────────────────────────┘
```

**P10 审查维度**：

| 维度 | 检查项 | 通过标准 |
|------|--------|---------|
| 架构健康 | 动画互斥、职责边界清晰 | 无冲突风险 |
| 质量门禁 | prefers-reduced-motion、动效开关 | 无障碍合规 |
| 基础设施 | 工具库完备、无重复定义 | DRY 原则 |
| 系统性风险 | 内存泄漏、性能瓶颈 | 长时间运行稳定 |
| Scope 合理 | 做减法、砍掉过度工程 | 投入产出比合理 |

**迭代终止条件**：P10 找不到任何 🔴 问题，且 UI 走查全部通过

**UI 走查清单**（与 P10 并行执行）：

```
## UI 走查报告模板

### 视觉一致性
- [ ] 主题适配: 4 个主题下颜色正确
- [ ] 棋子可见性: 深色/浅色背景下清晰
- [ ] 高对比度: 关键元素对比度足够

### 交互体验
- [ ] 点击反馈: 选中、移动、吃子有明确视觉反馈
- [ ] 动画流畅: 无卡顿、无闪烁
- [ ] 状态提示: 将军、获胜等状态清晰

### 移动端适配
- [ ] 375px 宽度: 内容完整可见 (grid minmax 130px)
- [ ] 触摸操作: 按钮可点击、棋子可选中
- [ ] 底部导航: 不遮挡内容 (padding 120px+)
- [ ] 模式选择: 参数面板不拥挤 (紧凑布局)

### 响应式修复参考值

```javascript
// GameLobby 卡片网格
gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))'  // 375px 可显示 2 列
className="gap-3 sm:gap-4"  // 响应式间距
className="p-3 sm:p-5"      // 响应式内边距

// PlatformView 底部导航
padding: '0 24px 120px'    // 防止遮挡

// ModeSelect 参数面板
padding: '16px 12px'       // 紧凑布局
gap: '8px'                 // 减小间距
```

### 总结
通过/失败项数量
```

P10 vs UI 走查分工：
- **P10**: 架构、内存泄漏、性能、无障碍合规
- **UI 走查**: 视觉、交互、移动端体验

**双轨迭代的好处**：
- P10 发现 3 个 🔴 问题（动画冲突、内存泄漏、颜色适配）
- UI 走查发现 3 个页面问题（卡片过窄、底部遮挡、面板拥挤）
- 两轮并行，效率翻倍

### Phase 4: 关键修复清单

| 问题类型 | 修复方案 |
|---------|---------|
| 动画冲突 | `enqueueAnimation()` 队列机制 |
| 内存泄漏 | useRef 单例 + 返回清理函数 |
| 无障碍 | `prefers-reduced-motion` + 手动开关 |
| 性能瓶颈 | RAF 节流 + OffscreenCanvas 复用 |
| 颜色适配 | CSS 变量 (accentPrimary) |
| CSS 膨胀 | 删除未使用的 @keyframes |

## 验证命令

每轮迭代必须执行：

```bash
pnpm test                    # 143 tests 全部通过
pnpm -F web build            # 构建成功
```

## 游戏插件扩展 Checklist

添加新游戏的标准流程：

```
□ packages/core/src/games/{game}/rules.js      - 规则引擎
□ packages/core/src/games/{game}/index.js       - 导出
□ packages/core/src/games/{game}/rules.test.js  - 测试
□ packages/core/index.js                        - 注册导出
□ apps/web/src/hooks/use{Game}Game.js           - 游戏 Hook
□ apps/web/src/components/{game}/Board.jsx      - 棋盘组件
□ apps/web/src/components/{game}/BoardArea.jsx  - 棋盘区域
□ apps/web/src/pages/{Game}PlayPage.jsx         - 游戏页面
□ apps/web/src/plugins/index.js                 - status: installed
□ apps/web/src/pages/PlayPage.jsx               - 添加路由
□ apps/web/src/lib/ai.worker.js                 - 添加 handler
```

## 做减法原则

P10 最重要的决策是"不做什么"：

**必须删除的**：
- 未被任何组件使用的 @keyframes
- 纯装饰性但增加 GPU 负担的效果
- 与核心体验无关的复杂动画

**延后处理的**：
- 架构级重构 (状态机模式)
- 缓动曲线统一 (CSS 变量 + JS 常量)
- 性能监控系统

## 成功模式

1. **P10 审查贯穿全生命周期** — 不仅是初期，每个迭代都要审查
2. **做减法和加功能同等重要** — 砍掉 5 个动画 = 减少维护成本
3. **无障碍合规是底线** — 不是可选项，是法律要求
4. **动画互斥是架构问题** — 必须在架构层解决，不能靠约定

## 文件结构

```
src/
├── lib/
│   └── animations.js          # 动效工具库
├── hooks/
│   └── useIntersectionObserver.js  # 滚动动画
├── components/
│   └── board/
│       ├── BoardCanvas.jsx    # Canvas 动画集成
│       └── VictoryOverlay.jsx # CSS 动画 + 粒子
├── contexts/
│   └── ThemeContext.jsx       # 动效开关
└── index.css                  # @keyframes + 工具类
```

---

## 补充：版本自动化 (semantic-release)

动效优化完成后，配置自动版本管理：

### 依赖安装

```bash
pnpm add -Dw semantic-release @semantic-release/changelog @semantic-release/git @semantic-release/github conventional-changelog-conventionalcommits
```

### .releaserc.json

```json
{
  "branches": ["main"],
  "plugins": [
    ["@semantic-release/commit-analyzer", {
      "preset": "conventionalcommits",
      "releaseRules": [
        { "type": "feat", "release": "minor" },
        { "type": "fix", "release": "patch" },
        { "type": "perf", "release": "patch" },
        { "type": "docs", "release": false },
        { "type": "chore", "release": false }
      ]
    }],
    ["@semantic-release/release-notes-generator", {
      "preset": "conventionalcommits"
    }],
    ["@semantic-release/changelog", {
      "changelogFile": "CHANGELOG.md"
    }],
    ["@semantic-release/npm", { "npmPublish": false }],
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "package.json"],
      "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
    }],
    ["@semantic-release/github"]
  ]
}
```

### .github/workflows/release.yml

```yaml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  release:
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, 'chore(release)')"
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0, persist-credentials: false }
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }  # semantic-release v25 需要 Node.js 22+
      - run: pnpm install --frozen-lockfile
      - run: pnpm test
      - run: pnpm -F @tg/web build
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**⚠️ semantic-release v25 踩坑**：

```
[semantic-release]: node version ^22.14.0 || >= 24.10.0 is required. Found v20.20.2.
```

必须将 `node-version` 设为 `22` 或更高，否则 release workflow 会失败。

### Cloudflare Pages + pnpm workspace 部署修复

**问题**：wrangler-action 使用 `pnpm add wrangler` 安装时失败

```
ERR_PNPM_ADDING_TO_ROOT  Running this command will add the dependency to the workspace root
```

**方案 A：直接使用 npx wrangler**

```yaml
# .github/workflows/deploy.yml
- name: Deploy to Cloudflare Pages
  env:
    CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
  run: npx wrangler pages deploy apps/web/dist --project-name=trusted-games-platform --branch=${{ github.ref_name }}
```

同时需要在 package.json 添加 wrangler 依赖：

```bash
pnpm add -Dw wrangler@3.90.0
```

**方案 B：使用 wrangler-action + packageManager**

```yaml
- name: Deploy to Cloudflare Pages
  uses: cloudflare/wrangler-action@v3
  with:
    apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
    command: pages deploy apps/web/dist --project-name=trusted-games-platform
    packageManager: npm  # 避免 pnpm workspace 限制
```

**推荐方案 A**，更简洁可靠。

### Commit 规范

| 类型 | 版本 | 示例 |
|------|------|------|
| `feat:` | minor | `feat: 添加落子动画` |
| `fix:` | patch | `fix: 修复动画冲突` |
| `perf:` | patch | `perf: 优化渲染性能` |
| `docs/chore/ci` | 不变 | `docs: 更新文档` |

---

## 实战案例：BoardCanvas 动画互斥锁

```javascript
// animations.js - Promise 队列实现
export function createAnimationQueue() {
  let queue = Promise.resolve()
  
  return function enqueue(fn) {
    const result = queue.then(fn, () => fn())
    queue = result.then(() => {}, () => {})
    return result
  }
}

// BoardCanvas.jsx - 使用互斥锁
const enqueueAnim = useRef(createAnimationQueue())

useEffect(() => {
  if (!lastMove) return
  enqueueAnim.current(async () => {
    const cancel = animate({ /* ... */ })
    await new Promise(r => setTimeout(r, duration))
    cancel()
  })
}, [lastMove])
```

## 实战案例：OffscreenCanvas 单例复用

```javascript
// 错误：每次依赖变化都创建新 Canvas
useEffect(() => {
  const offscreen = new OffscreenCanvas(...) // ❌ 内存泄漏
}, [board, hoverCell, ...])

// 正确：useRef 单例 + 独立初始化
const offscreenRef = useRef(null)

// 初始化（只执行一次）
useEffect(() => {
  offscreenRef.current = new OffscreenCanvas(...)
}, [])

// 渲染（状态变化时）
useEffect(() => {
  if (!offscreenRef.current) return
  const ctx = offscreenRef.current.getContext('2d')
  // ... 渲染逻辑
}, [board, hoverCell, ...])
```

## 实战案例：动效开关实现

```javascript
// ThemeContext.jsx
const [animationsEnabled, setAnimationsEnabled] = useState(() => {
  return localStorage.getItem('tg-animations') !== 'off'
})

const toggleAnimations = useCallback(() => {
  setAnimationsEnabled(prev => {
    const next = !prev
    localStorage.setItem('tg-animations', next ? 'on' : 'off')
    document.documentElement.setAttribute('data-animations', next ? 'on' : 'off')
    return next
  })
}, [])

// 初始化
useEffect(() => {
  document.documentElement.setAttribute('data-animations', animationsEnabled ? 'on' : 'off')
}, [animationsEnabled])
```

```css
/* index.css */
[data-animations="off"] *,
[data-animations="off"] *::before,
[data-animations="off"] *::after {
  animation-duration: 0.01ms !important;
  animation-delay: 0ms !important;
  transition-duration: 0.01ms !important;
  transition-delay: 0ms !important;
}
```

## 实战案例：createParticles 内存泄漏修复

```javascript
// 错误：无法清理
export function createParticles(container, options) {
  // ... 创建粒子
  setTimeout(() => {
    particles.forEach(({ element }) => element.remove())
  }, duration)
  // ❌ 组件卸载时 setTimeout 仍在运行
}

// 正确：返回清理函数
export function createParticles(container, options) {
  const particles = []
  let timeoutId = null
  
  // ... 创建粒子
  
  timeoutId = setTimeout(() => {
    particles.forEach(({ element }) => element?.parentNode?.removeChild(element))
  }, duration)
  
  // 返回清理函数
  return () => {
    if (timeoutId) clearTimeout(timeoutId)
    particles.forEach(({ element }) => element?.parentNode?.removeChild(element))
  }
}

// 使用时
useEffect(() => {
  if (!show) return
  const cleanup = createParticles(container, options)
  return cleanup  // 组件卸载时自动清理
}, [show])
```

## 实战案例：胜利线颜色适配主题

```javascript
// 错误：硬编码颜色，在某些主题下不可见
ctx.strokeStyle = '#ff3366'  // ❌ accentDanger

// 正确：使用 CSS 变量
const rootStyle = getComputedStyle(document.documentElement)
const accentColor = rootStyle.getPropertyValue('--accent-primary').trim()
ctx.strokeStyle = accentColor  // ✅ 4 个主题都可见
```
