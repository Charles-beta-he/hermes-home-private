MCP 服务器已配置: filesystem (npx, /Users/charles/Desktop/folder), time (uvx), memory (npx) — 同时生效于 Hermes (~/.hermes/config.yaml) 和 Claude (.claude/mcp.json)
§
项目: gomoku-react (trusted-games-platform), pnpm monorepo。GitHub: https://github.com/Charles-beta-he/trusted-games-platform。部署: Cloudflare Pages (npx wrangler)。CI: GitHub Actions + semantic-release (Node.js 22+)。4个游戏: gomoku/xiangqi/chess/go。v1.4.8, UIMax A+ 全满。每轮 Loop 要求 P10 自检 + UI 走查。内联样式迁移策略: 颜色→主题类, 布局→Tailwind, 保留动态样式。Discover 页面 + BottomNav 已上线。
§
关键教训: 删除文件前必须 grep 全项目残留引用 + 跑 pnpm build (不能只跑 pnpm test，因为 web 层无测试覆盖)。改文件后要同时跑 test + build 验证。
§
P10→P9→P8 三层架构验证有效：P10 定战略+做减法，P9 拆 Task Prompt，P8 执行。动效系统优化中，三轮审查修复 10 个问题，最终达到"无改进"状态。关键教训：无障碍合规 (prefers-reduced-motion) 必须在架构层解决，动画互斥需要队列机制防止冲突。
§
项目已配置 semantic-release 自动版本管理:
- .releaserc.json 配置 conventional commits
- .github/workflows/release.yml (Node.js 22)
- 版本规则: feat→minor, fix/perf/refactor→patch, docs/chore/ci→不变
- 首次发布: v1.0.0 (2026-04-17)
- GitHub Token 用于自动创建 Release 和 Tag
§
gomoku-react 动效系统架构:
- animations.js: RAF驱动动画库，easings/stagger/spring/sequence/createParticles/canvasAnimations
- BoardCanvas: 动画互斥锁 enqueueAnimation()，OffscreenCanvas 单例复用 useRef
- prefers-reduced-motion 支持 + data-animations="off" 属性禁用
- P10→P9→P8 三层 Loop 架构验证有效，10个问题全部闭环
- semantic-release v1.0.0 已发布，自动版本管理已配置
§
Canvas 像素尺寸关键教训：canvas 元素必须显式设置 canvas.width/canvas.height 属性，CSS style 的 width/height 只是显示尺寸，不影响实际渲染像素。OffscreenCanvas + drawImage 场景下，主 canvas 默认 300×150 会导致只显示部分内容。修复：在 useEffect 中设置 canvas.width = Math.round(CANVAS_PX * dpr)。
§
代码质量审计: 90%+ inline styles 使用 CSS vars 则 B 合理，继续迁移收益递减。响应式关键: px-8→px-4 sm:px-8，sm: 目标 2-3x md: 数量。Grid 背景需 opacity 0.5 + backgroundSize 60px 才不抢主体。CSS 工具类 (text-danger, bg-danger-subtle) 批量替换 inline var() 风格。v1.4.8, A+ 全满 (7轮), Discover 页面上线, 158 tests。BottomNav 4 项 + aria-current。
§
arc-dispatch v2: Lark→hermes pipeline。collector SQL dedup+token refresh。confirmer hermes分析+SKIPPED通知。executor hermes+session持久化+自审。validator解析verdict+重试计数。orchestrator --mode/--limit。12 tests passed。browser-harness: dogfood+visual-regression+uimax-audit，work/项目优化(Vue+Element桌面, Vue+Vant移动, React+Ant Design桌面)，移动端375px/桌面1280px视口测试。