---
name: visual-regression
description: "browser_vision 截图 diff 对比 — 自动检测 UI 视觉回归。截图存储 + AI 对比 + 差异报告。用于 UIMax 审计、迭代验证、CI 集成。"
license: MIT
tags: [visual-regression, screenshot, diff, uimax, qa, browser]
---

# Visual Regression — browser_vision 截图 diff 对比

> 通过 browser_vision 截图 + AI 分析，自动检测 UI 视觉变化和回归问题。

## When to Use

- UIMax 审计前后对比（修复前 vs 修复后）
- 代码变更后验证 UI 无回归
- 主题切换后检查渲染正确性
- 响应式布局验证（375px/768px/1280px）
- 用户说「截图对比」「视觉回归」「UI diff」

## Workflow

### Phase 1: 建立基线截图

在改动前，对所有关键页面截图并保存：

```bash
# 创建截图目录
mkdir -p .visual-regression/baseline
mkdir -p .visual-regression/current
```

关键页面清单：
1. `/` — Lobby 页面
2. `/discover` — 发现页面（卡片视图 + 列表视图）
3. `/play/gomoku` — 五子棋对局页
4. `/platform` — 在线平台页
5. `/styles` — 棋风中心页

截图流程：
```
browser_navigate(url)
browser_vision(question="Capture full page for visual regression baseline", annotate=false)
→ 保存 screenshot_path 到 baseline 目录
```

### Phase 2: 变更后截图

代码修改后，对相同页面再次截图：

```
browser_navigate(url)
browser_vision(question="Capture full page for visual regression comparison", annotate=false)
→ 保存 screenshot_path 到 current 目录
```

### Phase 3: AI Diff 对比

使用 vision_analyze 对比基线和当前截图：

```
vision_analyze(
    image_url=baseline_path,
    question="Compare this baseline screenshot with the current version. List ALL visual differences: layout changes, color changes, spacing changes, missing/added elements, alignment issues, text changes. Rate regression severity: NONE/LOW/MEDIUM/HIGH/CRITICAL."
)
```

或者使用 browser_vision 直接对比：

```
browser_vision(question="""
Compare this page with the expected design. Check for:
1. Layout shifts or misalignment
2. Color inconsistencies
3. Missing or extra elements
4. Text overflow or truncation
5. Spacing anomalies
6. Broken responsive behavior

Rate overall visual quality A-F and list any regressions.
""")
```

### Phase 4: 生成报告

输出格式：

```
=== Visual Regression Report ===

| 页面 | 基线 | 当前 | 差异 | 严重度 |
|------|------|------|------|--------|
| / | ✅ | ✅ | 无变化 | NONE |
| /discover | ✅ | ⚠️ | 筛选按钮间距增大 | LOW |
| /play/gomoku | ✅ | ✅ | 无变化 | NONE |
| /platform | ✅ | ❌ | 头像区域溢出 | HIGH |
| /styles | ✅ | ✅ | 无变化 | NONE |

总体: 4/5 通过, 1 个 LOW, 1 个 HIGH

HIGH 详情:
- /platform: 用户头像区域在 375px 下溢出边界
  基线: 头像正常显示
  当前: 头像被截断
  修复: 添加 overflow-hidden 或缩小头像尺寸
```

## 截图管理

### 目录结构

```
.visual-regression/
├── baseline/
│   ├── lobby.png
│   ├── discover.png
│   ├── discover-list.png
│   ├── play-gomoku.png
│   ├── platform.png
│   └── styles.png
├── current/
│   └── (同上)
├── diffs/
│   └── report-{date}.md
└── README.md
```

### 截图命名规范

`{page}-{variant}-{viewport}.png`

示例：
- `lobby-default-1280.png`
- `discover-list-375.png`
- `play-gomoku-ai-mode-768.png`

## 多视口验证

对每个页面在多个视口截图：

| 视口 | 宽度 | 用途 |
|------|------|------|
| mobile | 375px | iPhone SE |
| tablet | 768px | iPad |
| desktop | 1280px | 桌面端 |

浏览器工具不支持直接设置视口，可通过以下方式模拟：
- 375px: 检查 sm: 断点是否生效
- 768px: 检查 md: 断点是否生效
- 1280px: 默认视口

## 与 UIMax 集成

在 UIMax 审计流程中嵌入视觉回归检查：

```
1. UIMax Phase 1 (视觉审计) → 截图基线
2. 执行修复
3. UIMax Phase 1 重跑 → 截图当前
4. AI Diff 对比 → 确认无回归
5. UIMax Phase 3 (生成报告) → 包含回归检查结果
```

## 自动化脚本

```python
# scripts/visual-regression.py
import os, shutil
from datetime import datetime

PAGES = [
    ('/', 'lobby'),
    ('/discover', 'discover'),
    ('/discover', 'discover-list'),  # after clicking "查看全部"
    ('/play/gomoku', 'play-gomoku'),
    ('/platform', 'platform'),
    ('/styles', 'styles'),
]

def capture_baseline():
    """截取所有页面基线"""
    ts = datetime.now().strftime('%Y%m%d')
    outdir = f'.visual-regression/baseline-{ts}'
    os.makedirs(outdir, exist_ok=True)
    # browser_navigate + browser_vision for each page
    # save screenshots to outdir
    return outdir

def compare_with_baseline(current_dir, baseline_dir):
    """AI 对比基线和当前截图"""
    report = []
    for fname in os.listdir(baseline_dir):
        baseline = os.path.join(baseline_dir, fname)
        current = os.path.join(current_dir, fname)
        if os.path.exists(current):
            # vision_analyze 对比
            pass
    return report
```

## Pitfalls

1. **动画状态**: 截图时动画可能处于不同阶段，需等待动画完成或禁用动画
2. **动态内容**: 时间戳、随机 ID 等动态内容会导致每次截图不同
3. **字体渲染**: 不同环境下字体抗锯齿可能不同
4. **截图延迟**: React CSR 页面需等待渲染完成再截图
5. **浏览器版本**: 不同 Chrome 版本渲染可能有细微差异

## 技巧

- 截图前加 `browser_console(clear=True)` 确保无弹窗干扰
- 对比时标注「装饰性差异」vs「功能性回归」
- 保存每次迭代的截图历史，便于追踪长期变化
