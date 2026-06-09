---
type: concept
status: draft
created: 2026-06-08
tags: [local-brain, llm-wiki, knowledge-compiler, qdrant-boundary, evidence]
evidence_refs:
  - [[02-证据与原文/evidence/2026-06-08-weixin-llm-wiki-claude-obsidian]]
---

# Hermes evidence-backed LLM Wiki 知识编译层

## Core idea

在 Hermes 本地大脑中加入一层 `evidence-backed compiled knowledge`：把视频、网页、repo、长文、会话复盘等 raw sources 编译成结构化 markdown wiki，而不是每次查询时只靠 RAG 临时拼接。

核心区别：

- RAG：查询时检索 raw chunks，临时生成答案。
- LLM Wiki：新增资料时先编译进 wiki；之后查询读取已沉淀的概念页、项目页、对比页、索引和矛盾标记。

## Proposed local-brain layers

```text
Raw sources / evidence
  -> compiled wiki markdown
  -> recall index: FTS / Qdrant
  -> agent answer with citations
  -> optional promotion gate: skill / memory / taskpool / ADR
```

## Landing zones

- `02-证据与原文/evidence/`：视频、网页、repo、截图/OCR、transcript、metadata 等事实源记录。
- `03-知识库/`：LLM 编译后的概念页、项目页、对比页、索引页。
- `04-知识原子/`：可复用但尚未晋升为 skill 的经验原子。
- `05-实践与项目/tasks/`：需要执行的 governed task。
- `06-治理与评审/`：边界、评审、ADR、proof gate。

## Promotion rules

Wiki 内容默认只是知识投影，不能自动变成系统权威：

- 稳定流程 -> skill。
- 用户长期偏好 -> memory。
- 执行机会 -> taskpool。
- 架构决策 -> ADR。
- 状态变更 -> taskpool / ledger / API。
- 相似召回 -> FTS/Qdrant，但必须回链原文或 wiki 文件。

## Anti-drift rules

- 不把 wiki 当 taskpool SSOT。
- 不把 Qdrant 检索结果当事实源。
- 不把 LLM 编译的综合结论无来源化。
- 不自动覆盖高价值结论；高风险修改必须保留 diff/proof。
- 不把大量资料塞进 memory；memory 只存稳定偏好/事实。

## Lint checks

周期性检查：

- orphan pages；
- dead links；
- duplicate concepts；
- stale claims；
- source-less claims；
- 未区分 verified / inferred / speculative 的结论；
- wiki 结论没有回链 evidence；
- 可晋升为 skill/task/ADR 但仍滞留在 wiki 的内容。

## Initial implementation direction

最小可行方案不是先安装 Obsidian 插件，而是在本地大脑中建立目录规范和门禁：

1. `ingest-source`：把视频/文章/repo 写入 evidence note，并抽取候选概念/项目页。
2. `compile-wiki`：生成或更新 concept/project/comparison/index markdown。
3. `wiki-lint`：检查链接、来源、过期和重复。
4. `wiki-query`：回答时必须引用 wiki/evidence。
5. `promote-*`：通过人工或治理门晋升到 skill/memory/taskpool/ADR。

## Open question

是否需要建立专门的 `03-知识库/wiki/` 子目录，并把当前外部项目/视频 intake 统一迁入 `sources / concepts / projects / comparisons / indexes` 结构。
