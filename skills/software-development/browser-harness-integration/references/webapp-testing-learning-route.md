# Webapp Testing / Playwright 证据链学习路线

从零到一的渐进式学习路径，基于 Hermes 现有 browser-harness-integration 能力。

## Phase 1: 浏览器工具基础

### 学习目标
- 掌握 Hermes 浏览器工具的基本操作
- 理解 snapshot vs vision 的区别

### 步骤
1. 用 `browser_navigate` 打开一个 URL
2. 用 `browser_snapshot(full=true)` 查看完整页面结构
3. 用 `browser_vision(question="...", annotate=true)` 截图分析
4. 用 `browser_console(clear=true)` 检查 JS 错误
5. 用 `browser_click` / `browser_type` 交互

### 验证
- 能对任意 URL 完成：navigate → snapshot → vision → console 检查

## Phase 2: 探索性测试 (Dogfood)

### 学习目标
- 按 browser-harness workflow 对页面做探索性测试
- 理解 viewport 差异

### 步骤
1. 加载 `browser-harness-integration` skill
2. 对目标页面执行：截图 → console 检查 → 交互测试 → 问题收集
3. 分别在 desktop (1280px) 和 mobile (375px) viewport 测试
4. 记录发现的问题，按 severity 分类

### 验证
- 产出包含截图 + 问题列表的测试报告

## Phase 3: Playwright 截图证据链

### 学习目标
- 理解 Playwright Script + Screenshot + Log Evidence Chain 模式
- 能写可复跑的证据脚本

### 步骤
1. 阅读 `playwright-evidence-chain.mjs` 脚本结构
2. 理解 evidence bundle：scriptPath + commandLine + url + viewport + screenshot + browserEvents + summary
3. 使用 `--dry-run` 模式验证脚本计划
4. 实跑脚本，检查 evidence-summary.json 中的 assertions
5. 为自己的目标页面编写类似脚本

### 关键模式
```javascript
// 1. 从已有项目复用 Playwright，不安装
const requireFromProject = createRequire(path.join(projectDir, 'package.json'));
({ chromium } = requireFromProject('@playwright/test'));

// 2. 记录浏览器事件
page.on('console', msg => events.push({...}));
page.on('pageerror', err => events.push({...}));
page.on('requestfailed', req => events.push({...}));

// 3. 断言 + 截图 + 机器可读 summary
await page.screenshot({ path: screenshotPath, fullPage: true });
```

### 验证
- dry-run 输出 plannedChecks 和 plannedArtifacts
- 实跑 status=PASS，assertions 全部 true

## Phase 4: UI 质量审计 (UIMax)

### 学习目标
- 掌握 6 维度 A-F 评分
- 学会 code audit 扫描技巧

### 步骤
1. 加载 `uimax-audit` skill
2. 对页面做 visual audit（browser_vision + browser_console）
3. 对代码做 code audit（search_files 扫描 aria-/inline styles/breakpoints）
4. 生成 UIMAX_REPORT.md

### 验证
- 报告包含 6 维度评分 + P0/P1/P2 问题列表

## Phase 5: Pipeline 集成

### 学习目标
- 理解 browser-harness 在任务流水线中的位置
- 学会 evidence closeout 规则

### 步骤
1. 理解流程：build → dev server → harness → report → stop server
2. 学习 severity-based 通知（critical=fail, high=warn）
3. 学习 UI evidence level 分类（unit ≠ browser ≠ full-stack）
4. 把 browser-harness 集成到自动化任务流

### 验证
- 任务流水线中包含浏览器验证步骤

## Phase 6: 高级模式

### Mocked Auth + Mocked API
- 参考：`references/mocked-auth-mocked-api-local-ui-verification.md`
- 用途：auth-gated 页面的本地 UI 验证
- 限制：不等价于后端验收

### Full-stack Real Backend
- 参考：`references/fullstack-real-backend-verification.md`
- 用途：前后端联调验证
- 要求：本地前后端都可运行

### PRD Product Logic Guards
- 参考：`references/prd-product-logic-guards.md`
- 用途：业务逻辑不变量断言
- 要求：有 PRD/test ledger

### Mobile H5 Loop Gates
- 参考：`references/mobile-h5-loop-gates.md`
- 用途：移动端特殊检查（short viewport、safe-area、bottom nav）

## 常见陷阱

1. **不要从脚本截图声明 UI 验收**：脚本证明页面渲染，不证明完整业务流
2. **不要临时安装 Playwright**：从已有项目复用，或在项目本身声明依赖
3. **evidence path 要稳定**：避免写入会被覆盖的 test-results/；用 /tmp/<project>-<scope>-<date>/
4. **mock 不等于验收**：mocked auth/API 是开发检查，不是产品验收
5. **viewport 不够**：至少测 desktop + mobile；H5 还要测 short viewport
6. **console error 不等于 warning**：error 阻塞，warning 观察
