---
type: evidence
source_type: weixin_video
status: captured
created: 2026-06-08
tags: [llm-wiki, claude-code, obsidian, local-brain, evidence-backed-knowledge]
source_url: https://weixin.qq.com/sph/AamBAFf6gU
resolved_url: https://channels.weixin.qq.com/finder-preview/pages/sph?id=AamBAFf6gU
---

# 微信视频号：Claude Code 第二大脑 / Karpathy LLM Wiki 落地

## Source

- 原始链接：https://weixin.qq.com/sph/AamBAFf6gU
- 解析链接：https://channels.weixin.qq.com/finder-preview/pages/sph?id=AamBAFf6gU
- 标题/文案：Claude Code第二大脑！卡帕西LLM WiKi落地！ #AI工具 #AI编程 #llmwiki #claudecode
- 发布日期：2026年6月8日
- 作者：AI产品狙击手
- 页面可见互动：136 / 473 / 36 / 10

## Extracted signal

该视频指向 Karpathy LLM Wiki 模式在 Claude Code + Obsidian 方向的落地。核心不是普通 RAG，而是让 LLM 持续维护一套结构化、交叉引用、可演化的 markdown wiki。

候选项目/方向：

- `AgriciDaniel/claude-obsidian`：Self-organizing AI second brain for Obsidian + Claude Code。
- 相关方向：`SamurAIGPT/llm-wiki-agent`、`sdyckjq-lab/llm-wiki-skill`、`Ar9av/obsidian-wiki`、`Pratiyush/llm-wiki`。
- 原始思想源：Karpathy `LLM Wiki` gist。

## Hermes relevance

适合放入本地大脑，但必须分层：

- Raw evidence/source：权威事实源，不允许 LLM 修改。
- Compiled wiki：LLM 编译后的 markdown 知识层，可更新、可引用、可 lint。
- Recall index：FTS/Qdrant 只负责召回，必须回链 evidence/wiki 文件。
- Promotion gates：wiki 内容不能自动晋升到 memory/skill/taskpool/ADR；需经过对应门禁。

## Boundary

- 本地大脑中的 LLM Wiki 是 knowledge projection / compiled knowledge layer，不是 taskpool/ledger authority。
- 任务状态、done/blocked/claimed、proof gate 仍由 taskpool/ledger/API 控制。
- 结论必须保留来源、置信度和可回溯 evidence。

## Candidate next task

`评估 Karpathy LLM Wiki / Claude Obsidian 作为 Hermes evidence-backed 知识编译层`

验收建议：输出目录规范、source->wiki->recall->promotion gate 流程、lint 规则、与 Qdrant/memory/skill/taskpool 边界矩阵。
