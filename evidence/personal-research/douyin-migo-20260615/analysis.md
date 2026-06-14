# 抖音图文「Vibe Coding大赏｜Migo」分析

## 1. 内容事实摘要与引用证据

本次实际打开了抖音短链 `https://v.douyin.com/1_yrOBHcffc/`，服务端重定向到抖音图文页：

- canonical / note id：`https://www.douyin.com/note/7651151653328014633`
- 抖音 HTML 标题：`Vibe Coding大赏｜Migo。这个skill的灵感是 - 抖音`
- meta description 摘要：`Vibe Coding大赏｜Migo。这个skill的灵感是从@黄泽洲 Zachary Huang 获得的... 这是个啥。它是一个帮你做旅行攻...`
- 作者/发布时间/互动：`泽轩604于20260614发布在抖音，已经收获了91个喜欢`
- 关键词：`旅行攻略, AI工具, vibecoding大赏, AI新星计划`

页面只 SSR 暴露了 1 张图。下载并 OCR 后，主图读到的核心文字为：

> `Migo · 旅行领航`
> `把一趟旅行变成一个美观、可离线、手机优先的单文件 HTML 页面`
> `交互地图 · 每日时间轴 · 出发前订票提醒 · 行前须知 · 待选航班 · 片区价位酒店`
> `一个 Claude Code / Codex 通用 Skill（也可适配其他 Agent）`

进一步用主图/标题中的精确短语 `"Migo" "旅行领航"` 查询 GitHub API，命中仓库：

- `zexuanw958-svg/travel-plan-viz`
- repo description：`Migo · 旅行领航 —— 把旅行行程生成为单文件、可离线、手机优先的 HTML（交互地图+每日时间轴+出发前提醒）。Claude Code / Codex 通用 Skill（travel-plan-viz）。`
- README 明确：这是 `Claude Code / Codex 通用 Skill（也可适配其他 Agent）`，目标是把一句旅行需求或现成行程，生成可离线、手机优先、单文件 HTML 旅行页。

证据文件：

- `fetch_meta.json`：短链解析、HTTP 状态、最终 URL、headers。
- `douyin_response.html` / `douyin_response.txt`：抖音 SSR 页面原始内容。
- `image_01.png`：抖音图文主图。
- `image_01_ocr.txt`：主图 OCR。
- `repo_meta.txt`：GitHub repo API 响应。
- `readme.txt`：GitHub README 原文。

## 2. Migo / skill 方法拆解

Migo 不是单纯的“提示词模板”，而是一个轻量产品化的 Agent skill：

1. **输入模式双入口**
   - 从零规划：用户只给目的地 + 天数，例如“香港 4 天 3 晚”。
   - 现有计划转网页：用户粘贴已有行程/HTML，让 Agent 重组为更可用页面。

2. **输出物明确**
   - 单文件 HTML，移动端优先，可离线保存/截图。
   - 包含交互地图、每日时间轴、提醒、须知、候选航班/酒店、美食等旅行决策面。

3. **机械逻辑固化，审美/内容由 Agent 生成**
   README 描述的结构是“混合架构”：
   - `assets/map.js`：地图引擎，负责编号标记、路线、导航深链。
   - `assets/reminders.js`：提醒引擎，负责截止日期计算、清单/徽标渲染。
   - `assets/page-contract.md`：页面内容契约，规定区块数据。
   - `references/research-guide.md`：联网调研指南。
   - `references/design-guidelines.md`：内置美学准则。

4. **跨 Agent 迁移设计**
   安装方式覆盖 Claude Code / Codex；没有 skills 机制时，可直接把 `SKILL.md` 当指令喂给其他 Agent。

## 3. 对 Hermes / 任务池 / skill 体系的可迁移点

1. **Skill = 指令契约 + 可测试小引擎 + 样例产物**
   Hermes 现有 skill 可借鉴这种“不是纯说明书”的结构：
   - `SKILL.md` 负责编排；
   - `assets/*.js/py` 固化易错逻辑；
   - `references/*.md` 提供调研/设计/验收准则；
   - `samples/` 提供回归样例；
   - `test/` 验证机械逻辑。

2. **把高变创造环节和低变确定逻辑分层**
   旅行页的视觉表现每次可由 Agent 设计，但地图标记、提醒日期、内容契约这类易错点应由代码/测试固定。Hermes 的任务池也可按此模式拆：
   - 任务 framing / 报告表达：可由模型生成；
   - 生命周期门、证据结构、冲突边界、proof parsing：必须由确定性代码和 fixture 约束。

3. **单文件可交付物适合 Hermes 个人工作流**
   对个人研究、旅行、项目 brief、Lark 任务复盘，单文件 HTML/Markdown 包是一种很好的 closeout 形态：可归档、可读回、可截图、可转发，同时不依赖服务端。

4. **跨 Agent portability 对 Hermes brain overlay 有参考价值**
   Migo README 强调“没有 skills 机制也可用 SKILL.md”。Hermes 的 overlay/skill 也应保持可降级：结构化契约优先，但能输出一个通用 prompt bundle 供其他 Agent 消费。

5. **任务池 intake 可要求类似 artifact contract**
   对“外部 repo/社会媒体趋势吸收”任务，可要求至少包含：source evidence、capability delta、portable pattern、risk、whether-to-enqueue。Migo 这种 skill repo 本身就是一个可作为入池任务模板的样例。

## 4. 风险 / 不确定性

1. 抖音 SSR 页面只暴露主图与截断 description；完整图文说明可能在 App 内或客户端 JS 中，当前证据不能声称覆盖全部正文。
2. OCR 来自单张图，可能存在少量识别误差；关键短语已通过 GitHub README 交叉验证。
3. GitHub repo 是通过精确短语搜索命中的强相关仓库，但抖音正文未直接 SSR 出 GitHub 链接，因此“抖音作品对应该仓库”是高置信关联，不是页面内硬链接证明。
4. 不应直接自动安装该 skill 到 Hermes/Claude/Codex；第三方代码执行、联网调研和 HTML 生成都应走单独 human-gated intake/implementation。

## 5. 是否追加后续实现任务

建议追加，但不是“安装 Migo”本身，而是一个 Hermes-native P2 evolution/workflow 任务：

> 评估并吸收 `travel-plan-viz` 的 skill 产品化结构：将“SKILL 编排 + deterministic assets + page contract + research/design references + samples + tests”抽象为 Hermes skill-quality checklist 与 starter template，先做只读评估和模板，不自动安装第三方 skill。

建议验收证据：

- repo commit / README / SKILL.md / tests 的引用证据；
- Hermes skill starter template 或 checklist artifact；
- 一个本地 dry-run 示例，证明生成的 skill skeleton 可被 Hermes skill loader / docs 流程消费；
- 不执行第三方联网规划、不写入用户旅行数据、不外发。

## 结论

Migo 的核心价值不是“旅行攻略”本身，而是把 vibe coding 中一次性的创造性结果，沉淀为跨 Agent 可复用、可测试、可交付的 skill 产品形态。对 Hermes 最值得吸收的是这种产品化 skill 模板：明确输入/输出、把易错逻辑代码化、把研究和设计准则文档化、用样例和测试形成回归证据。
