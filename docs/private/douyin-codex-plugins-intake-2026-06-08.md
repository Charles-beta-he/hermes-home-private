---
type: evidence
source_type: douyin_video
status: captured
created: 2026-06-08
source_short_url: https://v.douyin.com/ng5L8-r5dnY/
resolved_url: https://www.douyin.com/video/7648950226031627571
author: AI挖掘机
published_at: 2026-06-08 17:13
title: 第4集 | Codex 干活飞起 #真实生活分享计划 #抖音玩法合伙人计划 #AI #Codex
---

# 抖音 Codex 插件/skill 视频证据

## 页面可见信息

- 作者：AI挖掘机
- 标题：第4集 | Codex 干活飞起 #真实生活分享计划 #抖音玩法合伙人计划 #AI #Codex
- 发布时间：2026-06-08 17:13
- 互动：赞 60、评论入口显示“抢首评”、收藏/分享等可见数值 11/1
- 大家都在搜：codex插件和skill

## 章节要点 OCR/DOM 提取

视频页自动章节写明：

1. hyperframes：根据需求生成页面和动效，可直接出片，可修改不满意的帧。
2. computer use：接住桌面上的重复操作，按步骤执行。
3. Chrome：打开页面搜索抓取，对比筛选资料，产出摘要和可用素材。
4. presentation：生成页面，检查文字和版式，尽量变成能交付的 PPT。
5. superpowers：先停一下，问清楚目标、素材、风险和标准，再拆计划、写任务、做检查。
6. 结语：插件让 Codex 从写代码变成能交付工作流的 agent。

## 本机 Codex 插件状态核验

命令：`codex plugin list`

已安装：
- browser@openai-bundled
- presentations@openai-primary-runtime
- documents@openai-primary-runtime
- spreadsheets@openai-primary-runtime
- gmail@openai-curated

未安装：
- hyperframes@openai-curated
- chrome@openai-bundled
- computer-use@openai-bundled
- superpowers@openai-curated

环境：
- Codex CLI: 0.137.0-alpha.4
- Node: v25.8.1
- FFmpeg: 8.1

## 初步判断

- presentations/browser：已安装，适合保留为 Codex 本地交付与前端验证能力。
- hyperframes：场景型 P2，适合产品 demo/作品集/短视频/动效原型，不应成为工程主链默认依赖。
- superpowers：理念/skill 结构有价值，但 Hermes 已有 taskpool/skill/proof gate，需做增量吸收，不应覆盖 Hermes 治理。
- chrome/computer-use：权限面大，只能显式授权、可审计启用；默认不安装。

## Hermes 边界

- Codex 插件是 action surface，不是事实源。
- Hermes taskpool/ledger/evidence 仍是 authority layer。
- Codex 产物必须回读验证。
- Chrome/Computer Use/Gmail 等接触真实账户/桌面/浏览器状态的能力必须有明确权限门禁。
